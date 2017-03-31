import argparse
from fabric import FabricBlockDev


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('device', type=int, nargs='?')
    return parser

if __name__ == '__main__':
    in_args = create_parser().parse_args()
    lb = FabricBlockDev().build_object(in_args)
    lb.execute()
