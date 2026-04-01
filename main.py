
# from flask import Flask, request, jsonify
# from google.cloud import bigquery
# import logging, re, os
# from twilio.rest import Client as TwilioClient

# app = Flask(__name__)
# logging.basicConfig(level=logging.INFO)
# bq = bigquery.Client()


# TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
# TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
# TWILIO_VERIFY_SERVICE_SID = os.environ["TWILIO_VERIFY_SERVICE_SID"]

# twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# TABLE_ID = "learning-486607.dialogflow_auth.users" 

# def normalize_to_e164_in(phone: str, default_cc="+91") -> str | None:
#     """
#     Normalize to E.164 for India default:
#       - Remove all non-digits except leading '+'
#       - 0XXXXXXXXXX -> XXXXXXXXXX
#       - 10-digit -> +91XXXXXXXXXX
#       - '+'+11..15-digit -> keep
#       - 11..15-digit no '+' -> prefix '+'
#     """
#     if not phone:
#         return None
#     phone = re.sub(r"(?!^\+)[^\d]", "", phone)

#     if re.fullmatch(r"0\d{10}", phone):
#         phone = phone[1:]

#     if re.fullmatch(r"\d{10}", phone):
#         return f"{default_cc}{phone}"

#     if phone.startswith("+") and 11 <= len(phone) <= 15:
#         return phone

#     if re.fullmatch(r"\d{11,15}", phone):
#         return f"+{phone}"

#     return None

# def check_user(phone_e164: str) -> str | None:
#     query = f"""
#         SELECT name
#         FROM `{TABLE_ID}`
#         WHERE phone = @phone
#         LIMIT 1
#     """
#     job = bq.query(
#         query,
#         job_config=bigquery.QueryJobConfig(
#             query_parameters=[bigquery.ScalarQueryParameter("phone", "STRING", phone_e164)]
#         ),
#     )
#     rows = list(job.result())
#     return rows[0].name if rows else None

# @app.get("/status")
# def status():
#     return "ok", 200

# @app.get("/debug")
# def debug():
#     ph = request.args.get("phone")
#     norm = normalize_to_e164_in(ph)
#     name = check_user(norm) if norm else None
#     return jsonify({"input": ph, "normalized": norm, "found": bool(name), "name": name})

# @app.post("/")
# def webhook():
#     body = request.get_json(silent=True) or {}
#     app.logger.info("DF session=%s lang=%s",
#                     (body.get("sessionInfo") or {}).get("session"),
#                     body.get("languageCode"))

#     params = (body.get("sessionInfo") or {}).get("parameters") or {}
#     phone = params.get("phone_number")  # set by Entry fulfillment

#     # Fallback directly from telephony payload if session param not set
#     if not phone:
#         phone = (body.get("payload") or {}).get("telephony", {}).get("caller_id")

#     app.logger.info("Raw caller phone: %r", phone)
#     phone_e164 = normalize_to_e164_in(phone, default_cc="+91")
#     app.logger.info("Normalized E.164 phone: %r", phone_e164)

#     user_name = check_user(phone_e164) if phone_e164 else None
#     authenticated = user_name is not None

#     # Build standard DF-CX response
#     msg = f"Authentication successful. Welcome {user_name}." if authenticated \
#           else "Authentication failed."

#     return jsonify({
#         "sessionInfo": {
#             "parameters": {
#                 "authenticated": authenticated,
#                 "user_name": user_name,
#                 "phone_number": phone_e164    # keep for later pages if needed
#             }
#         },
#         "fulfillmentResponse": {
#             "messages": [
#                 {"text": {"text": [msg]}}
#             ]
#         }
#     }), 200

# @app.post("/l1")
# def l1_webhook():
#     """
#     Dialogflow CX Standard webhook.
#     Expects two tags: sendOtp (start via call), verifyOtp (check code).
#     """
    
#     body = request.get_json(silent=True) or {}
#     tag = (body.get("fulfillmentInfo") or {}).get("tag")
#     params = (body.get("sessionInfo") or {}).get("parameters") or {}

#     # Caller ID from CX Phone Gateway payload OR from a session param.
#     phone_raw = params.get("phone_number") or (body.get("payload") or {}).get("telephony", {}).get("caller_id")
#     otp = params.get("otp")

#     phone_e164 = normalize_to_e164_in(phone_raw, default_cc="+91")
#     app.logger.info("L1 tag=%r phone_raw=%r phone_e164=%r otp=%r", tag, phone_raw, phone_e164, otp)

#     def respond(text, **extra_params):
#         return jsonify({
#             "sessionInfo": {"parameters": {"phone_number": phone_e164, **extra_params}},
#             "fulfillmentResponse": {"messages": [{"text": {"text": [text]}}]}
#         }), 200

#     if tag == "sendOtp":
#         if not phone_e164:
#             return respond("I couldn't read your phone number to send a code.", authenticated=False)
#         # Start Twilio Verify via CALL (voice) -> Twilio calls and speaks OTP
#         verification = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
#             .verifications.create(to=phone_e164, channel="call")
#         app.logger.info("verify.start status=%s", getattr(verification, "status", None))
#         return respond(
#             "I’m calling your number with a 6‑digit code now. Please enter the code and press #.",
#             authenticated=False, otp_channel="call"
#         )

#     if tag == "verifyOtp":
#         if not (phone_e164 and otp):
#             return respond("I need the 6‑digit code to verify.", authenticated=False)
#         check = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
#             .verification_checks.create(to=phone_e164, code=str(otp))
#         approved = (getattr(check, "status", "") == "approved")
#         app.logger.info("verify.check status=%s approved=%s", getattr(check, "status", None), approved)
#         if approved:
#             name = check_user(phone_e164)  # optional personalization
#             msg = f"Authentication successful. Welcome {name}." if name else "Authentication successful."
#             return respond(msg, authenticated=True, user_name=name)
#         else:
#             return respond("The code didn’t verify. Would you like me to resend?", authenticated=False)

#     # Default: if tag missing/mismatch
#     return respond("I’m here to test.", authenticated=False)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080)

from flask import Flask, request, jsonify
from google.cloud import bigquery
import logging, re, os
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ----------------- GCP CLIENTS -----------------
bq = bigquery.Client()

# ----------------- ENV (Twilio) -----------------
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_VERIFY_SERVICE_SID = os.environ["TWILIO_VERIFY_SERVICE_SID"]
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ----------------- CONFIG -----------------
TABLE_ID = "learning-486607.dialogflow_auth.users"  # project.dataset.table

# ----------------- HELPERS -----------------
def normalize_to_e164_in(phone: str, default_cc: str = "+91") -> str | None:
    """
    Normalize to E.164 for India by default:
      - Remove non-digits except a leading '+'
      - 0XXXXXXXXXX -> XXXXXXXXXX (strip leading '0' for 0+10-digit)
      - 10-digit -> +91XXXXXXXXXX
      - '+' + 11..15-digit -> keep as-is
      - 11..15-digit (no '+') -> prefix '+'
    """
    if not phone:
        return None
    # keep a leading '+', strip all other non-digits
    phone = re.sub(r"(?!^\+)[^\d]", "", phone)

    # 0XXXXXXXXXX -> XXXXXXXXXX
    if re.fullmatch(r"0\d{10}", phone):
        phone = phone[1:]

    # local 10-digit -> +CC
    if re.fullmatch(r"\d{10}", phone):
        return f"{default_cc}{phone}"

    # already looks like +<11..15>
    if phone.startswith("+") and 11 <= len(phone) <= 15:
        return phone

    # 11..15 digits without '+'
    if re.fullmatch(r"\d{11,15}", phone):
        return f"+{phone}"

    return None


def check_user(phone_e164: str) -> str | None:
    """Optional personalization: get name by phone from BigQuery."""
    query = f"""
        SELECT name
        FROM `{TABLE_ID}`
        WHERE phone = @phone
        LIMIT 1
    """
    job = bq.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("phone", "STRING", phone_e164)]
        ),
    )
    rows = list(job.result())
    return rows[0].name if rows else None


def df_respond(text: str, session_params: dict | None = None, http_status: int = 200):
    """Build a Dialogflow CX Standard webhook response."""
    payload = {
        "sessionInfo": {"parameters": session_params or {}},
        "fulfillmentResponse": {"messages": [{"text": {"text": [text]}}]},
    }
    return jsonify(payload), http_status


# ----------------- HEALTH/DEBUG -----------------
@app.get("/status")
def status():
    return "ok", 200


@app.get("/debug")
def debug():
    ph = request.args.get("phone")
    norm = normalize_to_e164_in(ph)
    name = check_user(norm) if norm else None
    return jsonify({"input": ph, "normalized": norm, "found": bool(name), "name": name})


# ----------------- (Optional) L0 -----------------
@app.post("/")
def webhook():
    """Your existing L0 logic (unchanged)."""
    body = request.get_json(silent=True) or {}
    app.logger.info("DF session=%s lang=%s",
                    (body.get("sessionInfo") or {}).get("session"),
                    body.get("languageCode"))

    params = (body.get("sessionInfo") or {}).get("parameters") or {}
    phone = params.get("phone_number") or (body.get("payload") or {}).get("telephony", {}).get("caller_id")
    app.logger.info("Raw caller phone: %r", phone)

    phone_e164 = normalize_to_e164_in(phone, default_cc="+91")
    app.logger.info("Normalized E.164 phone: %r", phone_e164)

    user_name = check_user(phone_e164) if phone_e164 else None
    authenticated = user_name is not None

    msg = (f"Authentication successful. Welcome {user_name}."
           if authenticated else "Authentication failed.")

    return df_respond(
        text=msg,
        session_params={
            "authenticated": authenticated,
            "user_name": user_name,
            "phone_number": phone_e164,
        },
    )


# ----------------- L1 (DTMF phone entry -> send OTP -> verify OTP) -----------------
@app.post("/l1")
def l1_webhook():
    """
    Dialogflow CX Standard webhook.
    Tags:
      - sendOtp  : Send OTP via Twilio Verify (default 'call', can override via session param 'otp_channel')
      - verifyOtp: Check OTP via Twilio Verify
    Assumptions:
      - 'phone_number' is captured via DTMF and present in session parameters.
      - 'otp' is captured via DTMF on the Enter OTP page.
    """
    body = request.get_json(silent=True) or {}
    tag = (body.get("fulfillmentInfo") or {}).get("tag")
    params = (body.get("sessionInfo") or {}).get("parameters") or {}

    # We now rely ONLY on the DTMF-captured number in session params.
    # Do not read caller_id in this L1 flow.
    phone_raw = params.get("phone_number")
    otp = params.get("otp")

    # Allow switching channel via session param if needed: 'call' (default) or 'sms'
    otp_channel = (params.get("otp_channel") or "sms").strip().lower()
    if otp_channel not in {"call", "sms"}:
        otp_channel = "sms"

    phone_e164 = normalize_to_e164_in(phone_raw, default_cc="+91")

    app.logger.info(
        "L1 tag=%r phone_raw=%r phone_e164=%r otp=%r channel=%s",
        tag, phone_raw, phone_e164, otp, otp_channel
    )

    def respond(text: str, **extra):
        # Keep 'phone_number' in session; and any extra state (authenticated, etc.)
        session_params = {"phone_number": phone_e164}
        session_params.update(extra)
        return df_respond(text=text, session_params=session_params)

    # -------------- sendOtp --------------
    if tag == "sendOtp":
        if not phone_e164:
            return respond("I couldn't read that number. Please enter the 10-digit number and press #.",
                           authenticated=False)

        try:
            verification = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
                .verifications.create(to=phone_e164, channel=otp_channel)
            app.logger.info("verify.start sid=%s status=%s",
                            getattr(verification, "sid", None),
                            getattr(verification, "status", None))

            if otp_channel == "call":
                prompt = "I’m calling that number with a 6‑digit code now. Enter the code and press #."
            else:
                prompt = "I’ve sent a 6‑digit code by SMS. Enter the code and press #."

            return respond(prompt, otp_channel=otp_channel, otp_sent=True)

        except TwilioRestException as e:
            app.logger.exception("verify.start failed code=%s status=%s", getattr(e, "code", None), e.status)
            # Friendly messaging for common trial restriction:
            # 21608: destination not verified on trial projects (Twilio blocks the send).
            if getattr(e, "code", None) == 21608:
                return respond(
                    ("I couldn’t send the code to that number because this Twilio trial "
                     "can only send to numbers verified in Twilio. Please enter a verified mobile number."),
                    authenticated=False, can_resend=False
                )
            # Generic error
            return respond("I couldn’t send the code right now. Please try again.", authenticated=False)

        except Exception:
            app.logger.exception("Unexpected error starting verification")
            return respond("Something went wrong starting verification. Please try again.", authenticated=False)

    # -------------- verifyOtp --------------
    if tag == "verifyOtp":
        if not (phone_e164 and otp):
            return respond("Please enter the 6‑digit OTP and press #.", authenticated=False)

        try:
            # check = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
            #     .verification_checks.create(to=phone_e164, code=str(otp))
            
            raw_otp = (str(otp) if otp is not None else "").strip()
            otp6 = raw_otp.zfill(6)
            app.logger.info("verifyOtp input raw_otp=%r otp6=%r", raw_otp, otp6)
            check = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(to=phone_e164, code=otp6)

            approved = (getattr(check, "status", "") == "approved")
            app.logger.info("verify.check sid=%s status=%s approved=%s",
                            getattr(check, "sid", None),
                            getattr(check, "status", None),
                            approved)

            if approved:
                name = check_user(phone_e164)  # optional personalization
                msg = f"Verification successful. Welcome {name}." if name else "Verification successful."
                return respond(msg, authenticated=True, user_name=name, verified_attempted=True)
            else:
                return respond("That code didn’t verify. Say ‘resend’ to try again.", authenticated=False, verified_attempted=True)

        except TwilioRestException as e:
            app.logger.exception("verify.check failed code=%s status=%s", getattr(e, "code", None), e.status)
            return respond("I couldn’t verify that code right now. Please try again.", authenticated=False)

        except Exception:
            app.logger.exception("Unexpected error checking verification")
            return respond("Something went wrong while verifying. Please try again.", authenticated=False)

    # -------------- default --------------
    return respond("I’m here to help. Please follow the prompts.", authenticated=False)


if __name__ == "__main__":
    # For local testing only; Cloud Run uses Gunicorn
    app.run(host="0.0.0.0", port=8080)