# -*- coding: utf-8 -*-
"""
@author: ShenWei
@description: sound shape code to compute ssc similarity for Chinese
              语音转文本，针对于相近音、混淆音，进行相似度计算。
              使用音形码进行中文相似度计算
"""

import collections
import json
import os
import sys

from loguru import logger
from pycorrector import config
from pycorrector.soundshapecode import ssc
from pycorrector.soundshapecode.variant_kmp import VatiantKMP
from pycorrector.soundshapecode.ssc_similarity.compute_ssc_similarity import computeSSCSimilaruty


class SoundShapeSim(object):
    def __init__(self,
                 custom_ssc_confusion_dict_or_path="",
                 similarity_threshold=0.8,
                 ssc_encode_way="SOUND"):
        self.name = "soundshapesimilarity"
        self.custom_ssc_confusion_dict_or_path = custom_ssc_confusion_dict_or_path
        self.custom_ssc_business_dict = {}
        self.custom_ssc_business_name_cnt = {}
        self.initialized_ssc = False
        self.similarity_threshold = similarity_threshold
        self.ssc_encode_way = ssc_encode_way
        # 加载SSC
        ssc.getHanziStrokesDict()
        ssc.getHanziStructureDict()
        ssc.getHanziSSCDict()
        self.kmp = VatiantKMP(similarity_threshold)

    def get_custom_ssc_business_vocab(self):
        business_dict, business_name_cnt = {}, {}
        with open(self.custom_ssc_confusion_dict_or_path,
                  "r",
                  encoding="utf-8") as reader:
            for line in reader:
                line = line.strip("\n")
                if line.startswith("#"):
                    continue
                strs = line.split("\t")
                if len(strs) != 3:
                    raise ValueError(f"Fine {self.custom_ssc_confusion_dict_or_path} find invalid format. {line}")
                name, alias, business = strs
                if business not in business_dict:
                    business_dict[business] = {alias: name}
                    business_name_cnt[business] = {name: 1}
                else:
                    alias2name = business_dict[business]
                    if alias not in alias2name and alias != "":
                        alias2name[alias] = name
                    else:
                        logger.debug(f"{business} has occured the same alias-[{alias}] or empty in the dictionary")
                    name2cnt = business_name_cnt[business]
                    if name not in name2cnt:
                        name2cnt[name] = 1
                    else:
                        name2cnt[name] += 1
        logger.debug(f"Load {self.custom_ssc_confusion_dict_or_path} Success.")
        return business_dict, business_name_cnt

    def check_ssc_initialized(self):
        if not self.initialized_ssc:
            self.custom_ssc_business_dict, self.custom_ssc_business_name_cnt = \
                self.get_custom_ssc_business_vocab()
            self.initialized_ssc = True

    def _get_custom_ssc_confusion_dict(self, path):
        """
        取自定义困惑集
        :param path:
        :return: dict, {variant: origin}, eg: {"交通先行": "交通限行"}
        """
        business_dict, business_name_cnt = {}, {}
        if path:
            if not os.path.exists(path):
                logger.warning("file not found.%s" % path)
                return business_dict, business_name_cnt
            else:
                with open(path,
                          "r",
                          encoding="utf-8") as reader:
                    for line in reader:
                        line = line.strip("\n")
                        if line.startswith("#"):
                            continue
                        strs = line.split("\t")
                        if len(strs) != 3:
                            raise ValueError(f"File {path} find invalid format. {line}")
                        name, alias, business = strs
                        if business not in business_dict:
                            business_dict[business] = {alias: name}
                            business_name_cnt[business] = {name: 1}
                        else:
                            alias2name = business_dict[business]
                            if alias not in alias2name and alias != "":
                                alias2name[alias] = name
                            else:
                                logger.debug(f"{business} has occured the same alias-[{alias}] in the dictionary")
                            name2cnt = business_name_cnt[business]
                            if name not in name2cnt:
                                name2cnt[name] = 1
                            else:
                                name2cnt[name] += 1
                logger.debug(f"Load {path} Success.")
        return business_dict, business_name_cnt

    def set_custom_ssc_path_or_dict(self, data):
        self.check_ssc_initialized()
        if isinstance(data, str):
            self.custom_ssc_business_dict, self.custom_ssc_business_name_cnt = \
                self._get_custom_ssc_confusion_dict(data)
        else:
            raise ValueError('custom_ssc_path_or_dict must be str path.')

    def gen_hash_from_ssc(self, alias2name, name2cnt):
        alias_hash_from_ssc = collections.defaultdict(list)
        name_hash_from_ssc = collections.defaultdict(list)
        # 获取别名的音形码
        aliases = list(alias2name.keys())
        for alias in aliases:
            hash_val = self.hash_ssc_for_word(alias)
            alias_hash_from_ssc[hash_val].append(alias)
        # 获取name的音形码
        names = list(name2cnt.keys())
        for name in names:
            hash_val = self.hash_ssc_for_word(name)
            name_hash_from_ssc[hash_val].append(name)
        logger.debug(f"Gen ssc hash size: alias_ssc[{len(alias_hash_from_ssc)}];"
                     f" name_ssc[{len(name_hash_from_ssc)}]; raw alias size: {len(aliases)};"
                     f" raw names size: {len(names)}")
        return alias_hash_from_ssc, name_hash_from_ssc

    def hash_ssc_for_word(self, ch_word):
        ch_word_ssc = ssc.getSSC(ch_word, self.ssc_encode_way)
        # 取每个汉字前两位作为hash值
        hash_val = ""
        for word_ssc in ch_word_ssc:
            hash_val += word_ssc[0:2]
        if hash_val == "":
            raise ValueError(f"Gen {ch_word} ssc exception.")
        return hash_val

    def compute_both_ssc_similarity(self, ch_word1, ch_word2):
        if len(ch_word1) != len(ch_word2):
            logger.error(f"{ch_word1} and {ch_word2} size is not equal.")
            return 0.0, False
        ch_word1_ssc = ssc.getSSC(ch_word1, self.ssc_encode_way)
        ch_word2_ssc = ssc.getSSC(ch_word2, self.ssc_encode_way)
        ssc_similarity = 0.0
        for idx in range(len(ch_word1_ssc)):
            ssc_similarity += computeSSCSimilaruty(ch_word1_ssc[idx],
                                                   ch_word2_ssc[idx], 
                                                   self.ssc_encode_way)
        
        ssc_similarity /= len(ch_word1)
        if ssc_similarity >= self.similarity_threshold:
            return ssc_similarity, True
        return ssc_similarity, False

    def ssc_similarity(self, business, slot):
        """
        中文相似音/混淆音相似度计算、并查找
        :param business: 业务名
        :param slot: 相近音/混淆音中文字符串
        : return: {}
        """
        ssc_result = {}
        if business == "" or slot == "":
            return ssc_result
        # 初始化
        self.check_ssc_initialized()
        # 基于业务查找对应的别名词典
        alias2name = self.custom_ssc_business_dict.get(business, {})
        name2cnt = self.custom_ssc_business_name_cnt.get(business, {})
        if len(alias2name) == 0:
            raise ValueError(f"Can't find business[{business}] alias2name")
        alias_hash_from_ssc, name_hash_from_ssc = \
            self.gen_hash_from_ssc(alias2name, name2cnt)
        # 1. 查找是否存在词典中
        if slot in name2cnt:
            name = alias2name[slot]
            ssc_result["name-alias"] = {"name": name, "code": 100, "cnt": 1}
        elif slot in name2cnt:
            cnt = name2cnt[slot]
            ssc_result["name-alias"] = {"name": slot, "code": 200, "cnt": cnt}
        # 2. 查找相近音/混淆音
        slot_hash_val = self.hash_ssc_for_word(slot)
        if slot_hash_val not in alias_hash_from_ssc \
            and slot_hash_val not in name_hash_from_ssc:
            ssc_result["ssc"] = {"code": -1,
                                 "alias_ssc": {},
                                 "name_ssc": {}}
        else:
            alias_ssc_dict, name_ssc_dict = {}, {}
            # 别名优先级高于真实名
            if slot_hash_val in alias_hash_from_ssc:
                # 2.1 发现别名相近音hash
                aliases = alias_hash_from_ssc[slot_hash_val]
                for alias in aliases:
                    ssc_similarity, status = \
                        self.compute_both_ssc_similarity(slot, alias)
                    if status:
                        alias_ssc_dict[alias] = ssc_similarity
            if slot_hash_val in name_hash_from_ssc:
                # 2.2 发现name相近音hash
                names = name_hash_from_ssc[slot_hash_val]
                for name in names:
                    ssc_similarity, status = \
                        self.compute_both_ssc_similarity(slot, name)
                    if status:
                        name_ssc_dict[name] = ssc_similarity
            code = -1
            if len(alias_ssc_dict) != 0 and len(name_ssc_dict) != 0:
                code = "303"
            elif len(alias_ssc_dict) != 0:
                code = "301"
            elif len(name_ssc_dict) != 0:
                code = "302"
            ssc_result["ssc"] = {"code": code,
                                 "alias_ssc": alias_ssc_dict,
                                 "name_ssc": name_ssc_dict}
        return ssc_result
