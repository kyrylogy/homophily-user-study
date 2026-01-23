#!/usr/bin/env python3
"""Simple CLI to test PROMPT_TEMPLATE and run interactive chats with the default or persona bot.

Usage examples:
  python cli_test.py --topic A --persona default
  python cli_test.py --topic B --persona A --call

Use `--call` to actually call the OpenAI API (requires OPENAI_API_KEY in .env).
"""
import argparse
import config
from openai import OpenAI
import sys


def get_persona_traits(label: str):
    if label == 'default':
        return {'O': 4.0, 'C': 4.0, 'E': 4.0, 'A': 4.0, 'N': 4.0}
    mu = config.CENTROIDS.get(label)
    if not mu:
        raise SystemExit(f"Unknown persona label: {label}")
    # mu = [E, A, C, ES, O]
    E, A, C, ES, O = mu
    N = 8.0 - ES
    return {'O': float(O), 'C': float(C), 'E': float(E), 'A': float(A), 'N': float(N)}


def build_system_prompt(topic_title: str, traits: dict):
    return config.PROMPT_TEMPLATE.format(topic=topic_title,
                                         O=traits['O'],
                                         C=traits['C'],
                                         E=traits['E'],
                                         A=traits['A'],
                                         N=traits['N'])


def interactive_loop(call_api: bool, system_prompt: str):
    print('\n=== System prompt ===\n')
    print(system_prompt)
    print('\nType messages to the assistant. Type `quit` or `exit` to stop.\n')

    if call_api and not config.OPENAI_API_KEY:
        print('OPENAI_API_KEY not set in environment; running local-only test. Use --call with a key set to invoke API.')
        call_api = False

    client = None
    if call_api:
        client = OpenAI(api_key=config.OPENAI_API_KEY)

    messages = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user = input('You: ')
        except (EOFError, KeyboardInterrupt):
            print('\nExiting.')
            return
        if user.strip().lower() in ('quit', 'exit'):
            print('Exiting.')
            return
        messages.append({"role": "user", "content": user})

        if call_api:
            try:
                resp = client.chat.completions.create(
                    model=config.BOT_MODEL,
                    messages=messages,
                    temperature=config.BOT_TEMPERATURE,
                    max_tokens=400
                )
                assistant = resp.choices[0].message.content
                print('\nAssistant:', assistant, '\n')
                messages.append({"role": "assistant", "content": assistant})
            except Exception as e:
                print('API error:', e)
        else:
            # Local echo mode: print the system prompt + user to help inspect formatting
            print('\n[Local test mode] System prompt was applied. The user message was:')
            print(user)
            print('\n(Use --call to send to OpenAI API.)\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', choices=['A', 'B'], default='A', help='Topic key to test (A or B)')
    parser.add_argument('--persona', choices=['default', 'A', 'C', 'O'], default='default', help='Persona to use')
    parser.add_argument('--call', action='store_true', help='Call OpenAI API')
    args = parser.parse_args()

    topic = config.TOPIC_A if args.topic == 'A' else config.TOPIC_B
    traits = get_persona_traits(args.persona)
    system_prompt = build_system_prompt(topic['title'], traits)
    interactive_loop(args.call, system_prompt)


if __name__ == '__main__':
    main()
