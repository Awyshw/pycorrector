# -*- coding: utf-8 -*-
"""Trie"""

import sys
import time

class TrieNode(object):
    def __init__(self):
        """
        Initialize data structure here.
        """
        self.data = {}
        self.is_word = False


class Trie(object):
    """
    trie树
    """
    def __init__(self):
        """
        Initialize data structure here.
        """
        self.root = TrieNode()

    def insert(self, word):
        """
        Inserts a word into the trie.
        :type word: str
        :rtype: void
        """
        node = self.root
        for chars in word:  # 遍历词语中的每个字符
            child = node.data.get(chars)  # 获取该字符的子节点
            if not child:  # 如果该自负不存在与树中
                node.data[chars] = TrieNode()  # 创建该字符节点
            node = node.data[chars]  # 节点为当前该字符节点
        node.is_word = True

    def search(self, word):
        """
        Returns if the word is in the trie.
        """
        node = self.root
        for chars in word:
            node = node.data.get(chars)
            if not node:
                return False
        return node.is_word  # 判断单词是否是完整的存在trie树中

    def startsWith(self, prefix):
        """
        Returns if there is any word in the trie 
        that start with the given prefix.
        :type prefix: str
        :rtype: bool
        """
        node = self.root
        for chars in prefix:
            node = node.data.get(chars)
            if not node:
                return False
        return True

    def get_start(self, prefix):
        """
        Returns words started with prefix
        :param prefix:
        :return: words(list)
        """
        def get_key(pre, pre_node):
            word_list = []
            if pre_node.is_word:
                word_list.append(pre)
            for x in pre_node.data.keys():
                word_list.extend(get_key(pre + str(x), pre_node.data.get(x)))
            return word_list

        words = []
        if not self.startsWith(prefix):
            return words
        if self.search(prefix):
            words.append(prefix)
            return words
        node = self.root
        for chars in prefix:
            node = node.data.get(chars)
        return get_key(prefix, node)

    def get_word_from_sentence(self,
                               sentence,
                               start_idx=0,
                               error_type="confusion"):
        """
        Returns words from sentence
        :params sentence:
        :return: words(list)
        """
        words_list = []
        pos = 0
        start_pos = 0
        node = self.root
        while pos < len(sentence):
            chars = sentence[pos]
            node = node.data.get(chars)
            if not node:
                pos += 1
                start_pos = pos
                node = self.root
                continue
            if node.is_word:
                words_list.append([sentence[start_pos:pos+1],
                                   start_idx + start_pos,
                                   start_idx + pos + 1,
                                   error_type])
                pos = pos+1
                start_pos = pos
                node = self.root
            else:
                pos += 1
        return words_list


if __name__ == "__main__":
    trie = Trie()
    trie.insert("神威")
    trie.insert("少波")
    trie.insert("因该")
    trie.insert("炒饭")
    sentence = sys.argv[1]
    t1 = time.time()
    print(trie.get_word_from_sentence(sentence))
    print("cost time:", time.time() - t1)
