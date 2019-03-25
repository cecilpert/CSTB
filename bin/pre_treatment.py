"""
Pre-processing to add a new genome to the database
"""

import os
import argparse
import json
import sys
import shutil
import pickle
import re
from Bio import SeqIO
from Bio import Entrez
from ete3 import NCBITaxa
from tqdm import tqdm
import couchBuild
import wordIntegerIndexing as decoding
import pycouch.wrapper as couchDB


# ARGUMENTS GESTION
def exists_file(parser, filename):
    """
    Check if the file exists and if it is a standard fasta file
    """
    # Check if the file exists
    if not os.path.isfile(filename):
        parser.error("Program terminated&The file {} does not exist !".format(filename))


def valid_fasta_file(parser, filename):
    """
    Check if the file exists and if it is a standard fasta file
    """
    # Check if the file exists
    exists_file(parser, filename)
    # Try to open it and check if it is a fasta file
    try:
        next(SeqIO.parse(filename, "fasta"))
    except Exception as err:
        parser.error("Program terminated&The file {} is not a fasta file !".format(filename))
    # If all is good, return the filename
    return filename


def valid_taxid(taxid):
    """
    Check if the taxon id given by the user is in the NCBI taxonomy
    database
    """
    ncbi = NCBITaxa()
    try:
        ncbi.get_lineage(taxid)
        return taxid
    except Exception as err:
        sys.exit("Program terminated&The taxon id given ({})\
                      is not in the NCBI taxonomy database !".format(taxid))


def check_metafile_exist(rfg, basename_file):
    """
    Check if the pickle and index file exist
    """
    return (os.path.exists(rfg + "/genome_index/" + basename_file + ".index") and
            os.path.exists(rfg + "/genome_pickle/" + basename_file + ".p"))


def parse_arg(subparser, command):
    """
    Definition
    """
    subparser.add_argument("-file", metavar="FILE",
                           type=lambda x: valid_fasta_file(subparser, x),
                           help="The path to the pickle file to add to the database")
    subparser.add_argument("-rfg", metavar="<str>",
                           help="The path to the reference genome folder",
                           required=True)
    subparser.add_argument("-url", metavar="<str>",
                           help="The end point", required=True)
    subparser.add_argument("-size", metavar="int", const=1000, nargs='?',
                           help="Maximal number of entry to add at a time")
    subparser.add_argument("-min", metavar="int", const=0, nargs='?',
                           help="Index of the first file to add to database")
    subparser.add_argument("-max", metavar="int", const=10, nargs='?',
                           help="Index of the last file to add to database")
    subparser.add_argument("-tree", metavar="<str>",
                           help="Path to the json tree", required=True)
    subparser.add_argument("-m", metavar="<str>",
                           help="DB volumes end-point mapper", required=True)
    if command == "add":
        subparser.add_argument("-dir", metavar="<str>",
                               help="The path to the pickle file to add to the database")
    return subparser


def args_gestion():
    """
    Take and treat arguments that user gives in command line
    """
    command = sys.argv[1] if len(sys.argv) > 1 else None
    # Argparsing
    parser = argparse.ArgumentParser(description="Pre-treatment to import new genomes")
    subparsers = parser.add_subparsers(help='commands')

    # Create metafile : pickle and index
    metafile_parser = subparsers.add_parser("metafile", help="Create the pickle file of the genome")
    metafile_parser.add_argument("-rfg", metavar="<str>",
                                 help="The path to the reference genome folder",
                                 required=True)
    metafile_parser.add_argument("-file", metavar="FILE",
                                 type=lambda x: valid_fasta_file(metafile_parser, x),
                                 help="The path to the fasta file",
                                 required=True)

    # Add to the database
    add_bdd_parser = subparsers.add_parser("add", help="Add the pickle file to the database")
    add_bdd_parser = parse_arg(add_bdd_parser, command)

    # Create metafile : pickle and index and add the pickle file to the database
    all_parser = subparsers.add_parser("all", help="Create the pickle file of the genome")
    all_parser = parse_arg(all_parser, command)

    args = parser.parse_args()
    if command == "add":
        if args.file and args.dir:
            parser.error("Program terminated&Missing file or directory")
        elif not args.file and not args.dir:
            parser.error("Program terminated&Choose file or directory, not both")
    return args, command


# CHECK IF THE TAXON ID IS ALREADY PRESENT AND COPY THE FASTA FILE
def name_organism(gb_data, accession, name):
    """
    Return the name of the organism with the GCF at the end
    """
    name = name.replace(accession, "")
    name = name.split(",")[0]
    name = name.replace("/", "_")
    name = name.replace("'", "")
    m = re.search("^\.[0-9] ", name).group()
    name = name.replace(m, "")
    name = name.strip()
    return name + " " + get_gcf_id(gb_data)


def get_accession_number(name):
    """
    Definition
    """
    accession = re.search("(N[CZ]\_[A-Za-z0-9]+)(\.[0-9])", name).group(1)
    print("Accession  : " + accession)
    return accession


def get_taxon_id(gb_data):
    """
    Definition
    """
    taxid = None
    taxon = gb_data.features[0].qualifiers["db_xref"]
    print("Longueur taxon list  : " + str(len(taxon)))
    for tax in taxon:
        if re.search("taxon", tax):
            print(tax)
            taxid = re.search("[0-9]+", tax).group()
            valid_taxid(taxid)
            print("Taxon ID  :  " + taxid)
            return taxid


def get_gcf_id(gb_data):
    """
    Definition
    """
    try:
        gcf = re.search("GCF\_[0-9]+\.[0-9]+", gb_data.dbxrefs[0]).group()
        print("GCF  :  " + gcf)
        return gcf
    except Exception as e:
        print("NO gcf")
        return None


def get_asm_id(gcf):
    """
    Definition
    """
    handle = Entrez.esearch(db="assembly", term="GCF_000223375.1")
    for i in handle:
        if re.search("<Id>", i):
            print(i)
    handle = Entrez.esummary(db="assembly",id=372888,report="full")
    for i in handle:
        if re.search("<AssemblyName>", i):
            print(i)
    return asm


def get_gcf_taxid(filename):
    """
    """
    seq_record = SeqIO.parse(filename, "fasta")
    name = next(seq_record).description
    accession = get_accession_number(name)
    Entrez.email = "example@gmail.com"
    res = Entrez.efetch(db="nuccore", id=accession, rettype="gb", seq_start=1, seq_stop=1)
    gb_data = SeqIO.read(res, "genbank")
    gcf = get_gcf_id(gb_data)
    taxid = get_taxon_id(gb_data)
    name = name_organism(gb_data, accession, name)
    return gcf, taxid, name


def check_genome_exists(filename, gcf, asm, taxid, rfg):
    """
    Create dictionnary for json file and gzip the fasta file
    """
    # Retrieve the name of the genome
    ref = gcf + "_" + asm

    with open(rfg + "/genome_ref_taxid.json", "r") as json_data:
        dic_ref = json.load(json_data)

    # Check if the reference is not in the dic_ref
    references = [ref_ref[0] for ref_ref in dic_ref.values()]
    tax_ids = [id[1] for id in dic_ref.values()]
    if ref in references:
        sys.exit("Program terminated&ERROR : This genome is already in the database")
    if taxid in tax_ids:
        sys.exit("Program terminated&ERROR : This taxon ID is already in the database")

    shutil.copyfile(filename, rfg + "/genome_fasta/" + ref + "_genomic.fna")

    return ref


# FIND ALL SGRNA
def complement_seq(sequence):
    """
    Function for turning a 5'-3' nucleotidic sequence into
    its 5'-3' reverse complement.
    """
    rev_comp = []
    complement = {"A" : "T", "C" : "G", "T" : "A", "G" : "C"}
    rev_comp = [complement[sequence[idx]] if sequence[idx] in complement.keys() else "N" for idx in range(len(sequence) - 1, -1, -1)]
    return "".join(rev_comp)


def build_expression(seq):
    """
    Build the regular expression by replacing the letter by iupac code or
    the letter itself
    """
    result = ''
    iupac_code = {'R': '[AG]', 'Y': '[CT]', 'S': '[GC]', 'W': '[AT]',
                  'K': '[GT]', 'M': '[AC]', 'B': '[CGT]', 'D': '[AGT]',
                  'H': '[ACT]', 'V': '[ACG]', 'N': '[ACGT]'}
    for letter in seq:
        if letter in iupac_code:
            result = result + iupac_code[letter]
        else:
            result = result + letter
    return result


def find_indices_sgrna(seq, pam):
    """
    Uses Regular expression matching of the pam motif to the reference genome
    to get the start positions (0-based) of each match
    """
    reg_exp = build_expression(pam)
    indices = [m.start() for m in re.finditer('(?=' + reg_exp + ')', seq, re.I)]
    return indices


def find_sgrna_seq(seq_list, len_seq, reverse, str_reverse, seq_dict, genome_seq, organism, ref):
    """
    Uses start index and the length of the sequence to get the sequence and
    fill the dictionary containing all sgRNA sequences with coordinates
    """
    for indice in seq_list:
        end = indice + len_seq
        seq = genome_seq[indice:end] if reverse else genome_seq[indice:end].reverse_complement()
        seq = str(seq)
        if seq not in seq_dict:
            seq_dict[seq] = {organism: {}}
        if ref not in seq_dict[seq][organism]:
            seq_dict[seq][organism][ref] = []
        seq_dict[seq][organism][ref].append(str_reverse + str(indice+1) + ',' +
                                            str(end) + ')')
    return seq_dict


def construct_in(organism, organism_code, rfg, pam="NGG", non_pam_motif_length=20):
    """
    Construct the sequences for first organism,
    with python regular expression research
    """
    print("SEARCH SGRNA")
    fasta_file = (rfg + '/genome_fasta/' + organism_code + '_genomic.fna')
    sgrna = "N" * non_pam_motif_length + pam

    seq_dict = {}

    for genome_seqrecord in SeqIO.parse(fasta_file, "fasta"):
        genome_seq = genome_seqrecord.seq
        ref = genome_seqrecord.id
        seq_list_forward = find_indices_sgrna(str(genome_seq),
                                              complement_seq(sgrna))
        seq_list_reverse = find_indices_sgrna(str(genome_seq), sgrna)

        seq_dict = find_sgrna_seq(seq_list_forward, len(pam) + non_pam_motif_length,
                                  False, "+(", seq_dict, genome_seq, organism, ref)
        seq_dict = find_sgrna_seq(seq_list_reverse, len(pam) + non_pam_motif_length,
                                  True, "-(", seq_dict, genome_seq, organism, ref)

    pickle_file = (rfg + "/genome_pickle/" + organism + ".p")
    pickle.dump(seq_dict, open(pickle_file, "wb"), protocol=3)
    return pickle_file


def indexation(name_file, rfg, pickle_file):
    """
    Code each sgrna sequence to a rank. With this, it is easier to compare
    sequences of several genomes
    """
    target_file = rfg + "/genome_index/" + name_file + '.index'

    total = decoding.indexPickle(pickle_file, target_file)
    print("Successfully indexed", total, "words\nfrom:", name_file, "\ninto:", target_file)


# CONSTRUCT THE NEW JSON TOPOLOGY TREE
def json_tree(bdd_path, tree_path):
    """
    Take the entire list of genomes and create the topology tree in json format
    """
    print('JSON TREE')
    os.system('python3 lib/tax2json.py ' + bdd_path + " " + tree_path)


def set_dic_taxid(dic_index_files, error_list, rfg):
    """
    Definition
    """
    with open(rfg + "/genome_ref_taxid.json", "r") as json_data:
        dic_ref = json.load(json_data)
    for filename in dic_index_files:
        if filename not in error_list:
            attr = dic_index_files[filename]
            filename = os.path.basename(filename)
            name = filename.replace(".index", "")
            dic_ref[name] = attr
    # Write the new json file with the new genome
    json.dump(dic_ref, open(rfg + "/genome_ref_taxid.json", 'w'), indent=4)


def add_to_database(files_to_add, end_point, iMin, iMax, batchSize, rules_file):
    """
    Add genomes in the database
    """
    if iMax > len(files_to_add):
        iMax = len(files_to_add)

    couchDB.setServerUrl(end_point)
    if not couchDB.couchPing():
        sys.exit("Program terminated&Impossible to connect to the database")

    with open(rules_file, "r") as rules_filin:
        couchDB.setKeyMappingRules(json.load(rules_filin))

    error_files = []
    for fName in files_to_add[iMin:iMax]:
        c = couchBuild.GenomeData(fName)
        # print("globing", fName, "#items", len(c))

        for i in tqdm(range(0, len(c), batchSize)):
            j = i + batchSize if i + batchSize < len(c) else len(c)
            d = c[i:j]
            r = couchDB.volDocAdd(d)
            for d in r:
                if not 'ok' in d:
                    print("Error here ==>", str(d))
                    error_files.append(fName)
    return error_files


if __name__ == '__main__':
    PARAM, COMMAND = args_gestion()
    ASM = "None"
    if COMMAND == "metafile" or COMMAND == "all":
        GCF, TAXID, NAME = get_gcf_taxid(PARAM.file)
        # Create dictionnary with all taxon ID
        REF_NEW = check_genome_exists(PARAM.file, GCF, ASM,
                                      TAXID, PARAM.rfg)
        PICKLE_FILE = construct_in(NAME, REF_NEW, PARAM.rfg)
        indexation(NAME, PARAM.rfg, PICKLE_FILE)
        print("SUCCESS&Created metafile for {}".format(NAME))

    if COMMAND == "add":
        DIC_INDEX_FILES = {}
        # Create list with all fasta files
        list_files = os.listdir(PARAM.dir) if PARAM.dir else [PARAM.file]
        # For each fasta file, retrieve the name of the pickle and index files
        # Then, check if they exist and create a list of path to index files
        for file_to_add in list_files:
            GCF, TAXID, NAME = get_gcf_taxid(file_to_add)
            if not check_metafile_exist(PARAM.rfg, NAME):
                sys.exit("Program terminated&Metafiles do not exist for {}".format(NAME))
            else:
                DIC_INDEX_FILES[PARAM.rfg + "/genome_index/" + NAME + ".index"] = [GCF + "_" + ASM, TAXID]

    elif COMMAND == "all":
        DIC_INDEX_FILES = {}
        DIC_INDEX_FILES[PARAM.rfg + "/genome_index/" + NAME + ".index"] = [REF_NEW, TAXID]

        print("DIC_INDEX_FILES == > {}".format(DIC_INDEX_FILES))

    # if COMMAND == "add" or COMMAND == "all":
    #     ERROR_LIST = add_to_database(list(DIC_INDEX_FILES.keys()), PARAM.url, PARAM.min, PARAM.max, PARAM.size, PARAM.m)
    #     set_dic_taxid(DIC_INDEX_FILES, [], PARAM.rfg)
    #     json_tree(PARAM.rfg, PARAM.tree)
