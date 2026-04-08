import sys
with open(r'd:\Email\email_sender.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines = lines[:167] # trim trailing duplicate functions
text = ''.join(lines)
text = text.replace('    \"\"\"\n    Sends up to 2 follow-ups to leads that have been sent an email but haven\'t replied\n    after 48 hours.\n    \"\"\"', '    # Sends up to 2 followups.')
with open(r'd:\Email\email_sender.py', 'w', encoding='utf-8') as f:
    f.write(text)
