with open(r'd:\Email\src\services\inbox_reader.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_except = '                    except Exception as e:\n        print(f\'Error checking inbox: {e}\')'
good_except = '                    except Exception as e:\n                        print("Failed to decode email body:", e)\n                        continue'
text = text.replace(bad_except, good_except)

end_function = '''
    if new_replies_count > 0:
        print(f'New replies processed: {new_replies_count}')
    else:
        pass # Handled by if not messages

    return new_replies_count
'''

text += end_function
with open(r'd:\Email\src\services\inbox_reader.py', 'w', encoding='utf-8') as f:
    f.write(text)
