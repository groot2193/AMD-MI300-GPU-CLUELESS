from flask import Flask, request, jsonify
from threading import Thread
import json
from openai import OpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import re
import uuid
from datetime import datetime, timedelta
import os
import psutil

# Constants
BASE_URL = "http://localhost:3000/v1"
MODEL_PATH = "/home/user/Models/deepseek-ai/deepseek-moe-16b-chat"

# Initialize Flask app
app = Flask(__name__)
received_data = []

def extract_json_from_markdown(text):
    """
    Extracts the first JSON object found inside a Markdown block (```json ... ```)
    or just inside any triple backticks.
    """
    # Remove Markdown code fencing if it exists
    code_block = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if code_block:
        return code_block.group(1).strip()
    
    # Fallback: Try to find a JSON object directly
    json_object = re.search(r"\{[\s\S]+\}", text)
    if json_object:
        return json_object.group(0).strip()

    raise ValueError("No JSON object found in model output.")

class MeetingSchedulerAgent:
    def __init__(self, client, model_path, token_folder="Keys/"):
        self.client = client
        self.model_path = model_path
        self.token_folder = token_folder

    def _call_model(self, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model_path,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def parse_email_for_meeting(self, email_text: str) -> dict:
        prompt = f"""
You are an assistant that helps in scheduling meetings.

Your task is to extract the following from the email:
1. From the input text, extract all unique email addresses and return them as a comma-separated list.
2. Meeting duration in minutes.
3. Time constraints (e.g., 'next week').
4. A 7 individual dates based on the time constraint (e.g., ["13-07-2025",..., "19-07-2025"]).
5. Subject of email , it need to show if its urgent, workshop , etc.
6. Email Content.

Rules:
- If any participant is just a name, append '@amd.com' to it.
- Return only a **valid JSON object** with the following fields:
  - participant_emails (string)
  - meeting_duration (integer)
  - time_constraints (string)
  - window (array of strings)
  - email_subject (string)
  - email_content (string)

Do not reason step-by-step. Do not explain. Do not use markdown. Return only JSON. Begin your output with {{
Email: {email_text}
"""
        raw = self._call_model(prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("❌ Invalid JSON from parse_email:\n", raw)
            raise

    def retrieve_calendar_events(self, user_email, start, end):
        token_path = self.token_folder + user_email.split("@")[0] + ".token"
        creds = Credentials.from_authorized_user_file(token_path)
        service = build("calendar", "v3", credentials=creds)
        events_result = service.events().list(
            calendarId='primary', timeMin=start, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()

        events = []
        for event in events_result.get('items', []):
            attendees = []
            try:
                attendees = [a['email'] for a in event['attendees']]
            except:
                attendees = ["SELF"]

            events.append({
                "StartTime": event["start"],
                "EndTime": event["end"],
                "NumAttendees": len(set(attendees)),
                "Attendees": list(set(attendees)),
                "Summary": event.get("summary", "No Summary")
            })
        return events

    def format_calendar_result(self, result):
        lines = []
        for entry in result:
            for email, blocks in entry.items():
                lines.append(f"\n📧 Email: {email}")
                for idx, block in enumerate(blocks):
                    for event in block:
                        summary = event.get("Summary", "No Summary")
                        attendees = ", ".join(event.get("Attendees", []))
                        num = event.get("NumAttendees", "Unknown")
                        start = event["StartTime"].get("dateTime") or event["StartTime"].get("date")
                        end = event["EndTime"].get("dateTime") or event["EndTime"].get("date")
                        lines.append(f"  🧾 {summary}: {start} → {end}, Attendees: {attendees}, NumAttendees: {num}")
        return "\n".join(lines)

    def set_attendees_with_events(self, attendee_emails, start, end):
        self.Attendees = []
        for email in attendee_emails:
            events = self.retrieve_calendar_events(email, start, end)
            self.Attendees.append({
                "email": email,
                "events": events
            })

    def schedule_meeting(self, original_email: str, emails: list) -> dict:
        meeting_json = self.parse_email_for_meeting(original_email)

        window_dates = [datetime.strptime(d, "%d-%m-%Y") for d in meeting_json["window"]]
        min_date = min(window_dates)
        max_date = max(window_dates)
        start_dt = min_date.strftime("%Y-%m-%dT00:00:00+05:30")
        end_dt = (max_date + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00+05:30")

        users = emails
        if isinstance(emails, str):
            users = [u.strip() for u in emails.split(",")]
        else:
            users = emails
        print(users)
        calendar_result = [{user: [self.retrieve_calendar_events(user, start_dt, end_dt)]} for user in users]

        self.set_attendees_with_events(users, start_dt, end_dt)

        result_str = self.format_calendar_result(calendar_result)

        scheduling_prompt = f"""
You are a smart calendar assistant with access to:
- A list of attendees (name + email)
- Each attendee's calendar events for the next 7 days

Your task is to schedule or reschedule meetings based on the email provided.

Prioritization rules:
1. Events with high‑priority subjects (e.g., 'Urgent', 'Workshop', 'Conference', 'Client meet', 'Meet Now', 'Server Down') must not be displaced.
2. Events with more attendees or high-priority tags increase the importance of that time slot.
3. Low‑priority events (e.g., tea breaks, casual/private events) may be rescheduled.

Important:
- Do NOT ask anyone to reschedule the meeting being scheduled (e.g., the one described in the email).
- Only ask someone to reschedule **their existing calendar event** if it **conflicts** with the new meeting **and**:
  1. It's low priority, and
  2. There are no other free slots within working hours (9 AM – 6 PM).

Constraints:
- Only schedule between 9:00 AM and 6:00 PM.
- When asked to schedule a meeting:
   a. Check if the requested day/time is available.
   b. If not, suggest another slot within 7 days.
   c. If low-priority events block, suggest rescheduling them.

Rescheduling behavior:
- If user wants to reschedule a meeting:
   • Check event priority.
   • If it's important or affects many people:
     - Ask why they want to change.
     - Explain what could happen.
     - Try to convince them politely to reschedule their event so you could schedule this event.
- If no slot is found, only then suggest minimal reschedules (with polite justification).

Email: {original_email}
Attendee Events:
{result_str}

Note:
- If an attendee's block contains the line "❌ No events found", it means they have no calendar events.
- In such cases, do not include any reschedule messages for that attendee.

Output format:
Return a valid JSON with:
- "EventStart": ISO datetime
- "EventEnd": ISO datetime
- "Duration_mins": integer
- "participants": comma-separated list of emails
- "reschedule_messages": array of objects:
  {{
    "to": string,
    "original_event": string,
    "original_time": string,
    "message": string
  }}
"""

        raw_output = self._call_model(scheduling_prompt)

        try:
            parsed_output = json.loads(raw_output)
        except (json.JSONDecodeError, ValueError) as e:
            print("❌ Invalid JSON from schedule_meeting:\n", raw_output)
            raise e

        final_result = {
            "Request_id": str(uuid.uuid4()),
            "Datetime": datetime.now().strftime("%d-%m-%YT%H:%M:%S"),
            "Location": "",
            "From": "",
            "Attendees": self.Attendees,
            "Subject": meeting_json.get("email_subject", ""),
            "EmailContent": meeting_json.get("email_content", original_email),
            "EventStart": parsed_output.get("EventStart", ""),
            "EventEnd": parsed_output.get("EventEnd", ""),
            "Duration_mins": str(parsed_output.get("Duration_mins", "")),
            "MetaData": {
                "reschedule_messages": parsed_output.get("reschedule_messages", [])
            }
        }

        return final_result

def your_meeting_assistant(data, emails):
    client = OpenAI(api_key="NULL", base_url=BASE_URL)
    agent = MeetingSchedulerAgent(client, model_path=MODEL_PATH)
    data_output = agent.schedule_meeting(data, emails)
    print(json.dumps(data_output, indent=2))
    return data_output

def find_and_kill(port):
    for conn in psutil.net_connections(kind='inet'):
        la = conn.laddr
        if la and la.port == port:
            pid = conn.pid
            if pid:
                proc = psutil.Process(pid)
                print(f"Killing PID {pid} ({proc.name()}) listening on port {port}")
                os.kill(pid, 9)
                return
    print(f"No process found listening on port {port}")

@app.route('/receive', methods=['POST'])
def receive():
    data = request.get_json()
    
    attendees = ", ".join([att["email"] for att in data.get("Attendees", [])])
    subject = data.get("Subject", "")
    email_content = data.get("EmailContent", "")
    
    req_prompt = f"Subject: {subject}\nAttendees: {attendees}\nEmail Content: {email_content}"
    print(f"\nConstructed Prompt:\n{req_prompt}")
    print(attendees)
    
    new_data = your_meeting_assistant(req_prompt, attendees)
    
    # Filter out messages where original_event == email_subject
    filtered_reschedules = [
        msg for msg in new_data.get("MetaData", {}).get("reschedule_messages", [])
        if msg.get("original_event") != subject
    ]
    
    # Update the original dict
    new_data["MetaData"]["reschedule_messages"] = filtered_reschedules
    
    # Safely copy keys if they exist
    for key in ["Request_id", "Datetime", "Location", "From"]:
        if key in data:
            new_data[key] = data[key]

    received_data.append(data)
    return jsonify(new_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
