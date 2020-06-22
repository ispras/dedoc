
import os

"""JOBLIB SETTINGS"""
# number of parallel jobs in some tasks as OCR
n_jobs = 4

"""API SETTINGS"""
# max file size in bytes
max_content_length = 512 * 1024 * 1024
# application port
api_port = int(os.environ.get('DOCREADER_PORT', '1231'))

"""LINE CLASSIFIER PARAMETERS"""
intermediate_data_path = None

"""TABLE RECOGNIZER SETTINGS"""
debug_table_mode = False
min_h_cell = 12
min_w_cell = 20
type_top_attr = 1
type_left_top_attr = 2
type_left_attr = 3
max_vertical_extended = 20

path_cells = "/tmp/backend_claw/out_tables/data_imgs/Cells/"
path_detect = "/tmp/backend_claw/out_tables/data_imgs/detect_lines/"
rotate_threshold = 0.3
