#!/usr/bin/env python3

from compare_trees import parse_args, config_logging, main

if __name__ == '__main__':
    args = parse_args()
    config_logging(args.loglevel)
    exit(main(args))
