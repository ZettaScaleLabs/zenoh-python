# Copyright (c) 2017, 2020 ADLINK Technology Inc.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors:
#   ADLINK zenoh team, <zenoh@adlink-labs.tech>

import asyncio
import sys
import time
import argparse
import json
import zenoh
from zenoh import config, Sample
from zenoh.queryable import EVAL


async def main():
    # --- Command line argument parsing --- --- --- --- --- ---
    parser = argparse.ArgumentParser(
        prog='z_eval',
        description='zenoh eval example')
    parser.add_argument('--mode', '-m', dest='mode',
                        choices=['peer', 'client'],
                        type=str,
                        help='The zenoh session mode.')
    parser.add_argument('--peer', '-e', dest='peer',
                        metavar='LOCATOR',
                        action='append',
                        type=str,
                        help='Peer locators used to initiate the zenoh session.')
    parser.add_argument('--listener', '-l', dest='listener',
                        metavar='LOCATOR',
                        action='append',
                        type=str,
                        help='Locators to listen on.')
    parser.add_argument('--key', '-k', dest='key',
                        default='/demo/example/zenoh-python-eval',
                        type=str,
                        help='The key expression matching queries to evaluate.')
    parser.add_argument('--value', '-v', dest='value',
                        default='Eval from Python!',
                        type=str,
                        help='The value to reply to queries.')
    parser.add_argument('--config', '-c', dest='config',
                        metavar='FILE',
                        type=str,
                        help='A configuration file.')

    args = parser.parse_args()
    conf = zenoh.config_from_file(
        args.config) if args.config is not None else zenoh.Config()
    if args.mode is not None:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect is not None:
        conf.insert_json5("connect/endpoints", json.dumps(args.connect))
    if args.listener is not None:
        conf.insert_json5("listeners", json.dumps(args.listener))
    key = args.key
    value = args.value

    # Note: As an example the concrete implementation of the eval callback is implemented here as a coroutine.
    #       It checks if the query's value_selector (the substring after '?') is a float, and if yes, sleeps for this number of seconds.
    #       Run example/asyncio/z_get_parallel.py example to see how 3 concurrent get() are executed in parallel in this z_eval.py

    async def eval_corouting(query):
        opt = query.value_selector[1:]
        try:
            sleep_time = float(opt)
            print("  Sleeping {} secs before replying".format(sleep_time))
            await asyncio.sleep(sleep_time)
        except ValueError:
            pass
        print("  Replying to query on {}".format(query.selector))
        reply = "{} (this is the reply to query on {})".format(
            value, query.selector)
        query.reply(Sample(key_expr=key, payload=reply.encode()))

    async def eval_callback(query):
        print(">> [Queryable ] Received Query '{}'".format(query.selector))
        # schedule a task that will call eval_corouting(query)
        asyncio.create_task(eval_corouting(query))

    # initiate logging
    zenoh.init_logger()

    print("Opening session...")
    session = await zenoh.async_open(conf)

    print("Creating Queryable on '{}'...".format(key))
    queryable = await session.queryable(key, EVAL, eval_callback)

    print("Enter 'q' to quit......")
    c = '\0'
    while c != 'q':
        c = sys.stdin.read(1)
        if c == '':
            time.sleep(1)

    await queryable.close()
    await session.close()

asyncio.run(main())
