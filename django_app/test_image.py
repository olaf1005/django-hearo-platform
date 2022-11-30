from tartar import GetLucky
from infrared import Context

import random

gl = GetLucky(Context("prod.config"))
gl.image_upload(random.randint(0, 1000), "tests/testimage.png", "admin", "normal")
