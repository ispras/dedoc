'''import os
os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + \
                               ':' + os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))'''
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))