# -*- coding: utf-8 -*-
import sys

sys.path.append("../")

import pycorrector
from pycorrector import SoundShapeSim

if __name__ == "__main__":
    slot = sys.argv[1]
    sscs = SoundShapeSim(custom_ssc_confusion_dict_or_path="../../spelling_correct/data/vocab.txt")
    sscs.set_custom_ssc_path_or_dict('../../spelling_correct/data/vocab.txt')
    business = "aipark_office"
    result = sscs.ssc_similarity(business, slot)
    print(result)
