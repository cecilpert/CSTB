"""
    Translate a dictionary of constant-length CRISPR motifs into an ordered set of integer, using base4 encoding.
    Usage:
        wordIntegerIndexing.py <pickledDictionary> [--out=<outFile>]

    Options:
        -h --help                               Show this screen
        -o <outFile>, --out <outFile>           Name of the output file [default : ./pickledDictionary.index]

"""

import os
import pickle
import math
from docopt import docopt


def indexPickle(file_path, target_file):
    """
    Take a pickle file, code it and write it in a file
    """
    p_data = pickle.load(open(file_path, "rb"))
    word_list = list(p_data.keys())
    data = sorted([weightWord(w, ["A", "T", "C", "G"], len(word_list[0])) for w in word_list])

    with open(target_file, "w") as filout:
        filout.write(str(len(data)) + "\n")
        for coding_int in data:
            filout.write(str(coding_int) + "\n")

    return len(data)


def weightWord(word, alphabet, length=None):
    """
    Code a word by base len(alphabet) and return this int
    """
    rank = 0
    if length:
        if length != len(word):
            raise ValueError("Irregular word length " + str(len(word)) +
                             " (expected " + str(length) + ")")
    for i, letter in enumerate(word[::-1]):
        wei = alphabet.index(letter)
        base = len(alphabet)
        rank += wei * pow(base, i)
    return rank


def decode(rank, alphabet, length=20):
    """
    Decode the rank (int) to a word according to an alphabet given
    """
    word = ""
    base = len(alphabet)
    for i in range(length - 1, -1, -1):
        index = math.trunc(rank / pow(base, i))
        word += alphabet[index]
        rank = rank % pow(base, i)
    return word


if __name__ == "__main__":
    ARGUMENTS = docopt(__doc__, version='wordIntegerIndexing 1.0')

    TARGET_FILE = ('.'.join(os.path.basename(ARGUMENTS['<pickledDictionary>']).split('.')[0:-1])
                   + '.index')
    if ARGUMENTS['--out']:
        TARGET_FILE = ARGUMENTS['--out']

    TOTAL = indexPickle(ARGUMENTS['<pickledDictionary>'], TARGET_FILE)
    print("Successfully indexed", TOTAL, "words\nfrom:",
          ARGUMENTS['<pickledDictionary>'], "\ninto:", TARGET_FILE)
