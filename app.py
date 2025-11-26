# whatsapp-ai-bot
# My AI customer support bot
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import google.generativeai as genai
import os
import re

app = Flask(__name__)

# === CONFIG ===
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
twilio_client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_TOKEN'))

# === ALL VENDORS – ADD NEW CLIENTS HERE (30 seconds each) ===
VENDORS = {
    "mama put": {
        "name": "Mama Put Jollof Palace",
        "menu": "Jollof ₦2500, Egusi+Poundo ₦3500, Fried Rice ₦2500, Chicken ₦1500",
        "payment": "https://paystack.com/pay/mamaput",
        "owner": "+2348033332211"
    },
    "kay barber": {
        "name": "Kay Barbing Salon",
        "menu": "Haircut ₦3000, Dye ₦8000, Shave ₦1500",
        "payment": "https://paystack.com/pay/kaybarber",
        "owner": "+2348077778899"
    },
    "tolu tailor": {
        "name": "Tolu Tailoring",
        "menu": "Native ₦25k–₦60k, Suit ₦80k–₦150k",
        "payment": "https://paystack.com/pay/tolutailor",
        "owner": "+2348055554433"
    }
    # ← Add new clients here
}

def find_vendor(text):
    text = text.lower().strip()
    for key in VENDORS:
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return VENDORS[key]
    return None

def forward_to_owner(vendor, msg, customer):
    if vendor and vendor.get("owner"):
        body = f"NEW ORDER\nfrom {customer}\nVendor: {vendor['name']}\n\n{msg}"
        twilio_client.messages.create(
            from_=f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
            to=f"whatsapp:{vendor['owner']}",
            body=body
        )

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming = request.values.get('Body', '').strip()
    customer = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    vendor = find_vendor(incoming)

    if vendor:
        forward_to_owner(vendor, incoming, customer)
        prompt = f"You are friendly staff for {vendor['name']}. Menu: {vendor['menu']}. Payment: {vendor['payment']}. Reply warmly in Pidgin+English. Customer said: {incoming}"
        reply = model.generate_content(prompt).text.strip()
        msg.body(reply)
    else:
        vendors = "\n".join([f"• {k.replace('_', ' ').title()}" for k in VENDORS.keys()])
        msg.body(f"Welcome! 🙌\nWhich shop you dey find today?\n\n{vendors}\n\nJust type the name or part of it!")

    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
