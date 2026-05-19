content = open('main.py', 'r', encoding='utf-8').read()

old = "    setup_scheduler(app)\n\n    logger.info"
new = "    logger.info"

new_app = '''async def post_init(app):
    setup_scheduler(app)

'''

content = content.replace("def main():", new_app + "def main():")
content = content.replace(".token(TELEGRAM_TOKEN).build()", ".token(TELEGRAM_TOKEN).post_init(post_init).build()")
content = content.replace(old, "    logger.info")

open('main.py', 'w', encoding='utf-8').write(content)
print('Fatto!')