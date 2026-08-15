import os
import requests
import time

API_URL = "http://127.0.0.1:8000"

def simulate_flow():
    print("1. Submitting intake request...")
    res = requests.post(f"{API_URL}/intake", json={
        "message": "Hi, there is water coming through the ceiling in apartment 3C.",
        "channel": "Email"
    })
    if res.status_code != 200:
        print("Intake failed:", res.text)
        return
        
    req_id = res.json()["maintenance_request"]["id"]
    print(f"Request created: {req_id}. Status: {res.json()['maintenance_request']['status']}")
    
    print("\n2. Dispatching to vendor...")
    res = requests.post(f"{API_URL}/simulate/dispatch/{req_id}")
    print(res.json())
    
    print("\n3. Vendor replies with slot...")
    res = requests.post(f"{API_URL}/simulate/message", json={
        "request_id": req_id,
        "sender": "VENDOR",
        "message": "We can do Thursday afternoon between 14:00-17:00."
    })
    print(res.json())
    
    print("\n4. Tenant asks for another day (forcing renegotiation)...")
    res = requests.post(f"{API_URL}/simulate/message", json={
        "request_id": req_id,
        "sender": "TENANT",
        "message": "I am not home on Thursday. Can we do Friday morning?"
    })
    print(res.json())
    
    print("\n5. Vendor agrees to Friday...")
    res = requests.post(f"{API_URL}/simulate/message", json={
        "request_id": req_id,
        "sender": "VENDOR",
        "message": "Friday morning 9am works for us."
    })
    print(res.json())
    
    print("\n6. Tenant agrees...")
    res = requests.post(f"{API_URL}/simulate/message", json={
        "request_id": req_id,
        "sender": "TENANT",
        "message": "Perfect, Friday 9am is great."
    })
    print(res.json())
    
    print("\n7. Fetching final state...")
    res = requests.get(f"{API_URL}/requests/{req_id}")
    final_state = res.json()
    print(f"Final Status: {final_state['request']['status']}")
    print("Work Orders:", len(final_state['work_orders']))
    print("Communication Logs:")
    for log in final_state['logs']:
        print(f"  [{log['sender']}] {log['message']}")

if __name__ == "__main__":
    if os.environ.get("OPENAI_API_KEY", "dummy_key_to_prevent_init_crash") == "dummy_key_to_prevent_init_crash":
        print("Please export OPENAI_API_KEY to run the simulation against the LLM.")
    else:
        simulate_flow()
