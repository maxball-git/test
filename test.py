import argparse
from fabric import FabricBlockDev


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('device', type=int, nargs='?')
    return parser

if __name__ == '__main__':
    in_args = create_parser().parse_args()
    #in_args.device = 1
    lb = FabricBlockDev().build_object(in_args)
    lb.execute()
