#!/usr/bin/env python3
"""
Traverse a phylogeny tree and find common nodes for selected organism and excluded organism
Return a list of path node and the list of included and excluded organism
not under nodes
"""


import json
import argparse
import pickle
from ete3 import NCBITaxa
import intersection as inter

DEBUG = False


def args_gestion():
    """
    Take and treat arguments that user gives in command line
    """
    # Argparsing
    parser = argparse.ArgumentParser(description="Allgenomes program.")
    parser.add_argument("-gi", metavar="<str>",
                        help="The organisms to search inclusion in.",
                        required=True)
    parser.add_argument("-gni", metavar="<str>",
                        help="The organisms to search exclusion from",
                        required=True)
    parser.add_argument("-rfg", metavar="<str>",
                        help="The path to the reference genome folder")
    return parser.parse_args()


def setup_application(parameters, dict_organism_code):
    """
    Processes the arguments to be usable for research
    """
    org_selected = parameters.gi.split('&')
    org_excluded = parameters.gni.split('&')
    org_selected = [i for i in org_selected if i in dict_organism_code]
    org_excluded = [i for i in org_excluded if i in dict_organism_code]
    # List of taxon ID of included genome
    taxid_in = [dict_organism_code[sp][1] for sp in org_selected]
    # List of taxon ID of excluded genome
    taxid_notin = [dict_organism_code[sp][1] for sp in org_excluded]
    return taxid_in, taxid_notin


def create_topo_tree(dict_org):
    """
    Create a topology tree with the organism dictionary given in parameter
    """
    # List of taxon ID of all genomes
    all_spc = [dict_org[sp][1] for sp in dict_org]
    if DEBUG: all_spc = [dict_org[sp][1] for sp in PARAM.gi.split('&')]
    all_spc = ['479432', '479433', '653045', '749414', '48']
    all_spc = ["261317", "372461", "1495769"]
    # Create the entire topology tree
    ncbi = NCBITaxa()
    return ncbi.get_topology(all_spc)


def traversing_tree(subtree, list_taxid):
    """
    Check if children of a given node are all entered by user. If the child is
    a subnode, then the same thing is done for its children.
    If all leaves have been entered, return true else return false
    """
    # Retrieve name of all sisters leaves
    names_sister = [pop.name for pop in subtree.children if pop.is_leaf()]
    # Check all names leaves have been entered by user else return false, this node cannot be used
    if not set(names_sister).issubset(list_taxid):
        return False

    # Retrieve all sub-nodes
    names_subnodes = [pop for pop in subtree.children if not pop.is_leaf()]
    if names_subnodes:
        for subnode in names_subnodes:
            # Check all leaves of sub_nodes have been entered by user
            if not traversing_tree(subnode, list_taxid):
                return False
    # The node can be used
    return True


def issubnode(node_ref, nodes_name):
    """
    Check if a given node is a child or a parent of a list of nodes.
    If it is a child, the given node is not appended to the list, else it is
    appended to the list. Moreover, if it is a parent to a node in the list,
    this node is removed
    """
    if node_ref.name in nodes_name:
        return nodes_name
    # Retrieve names of all children of the node given
    children_name = [child.name for child in node_ref.children if not child.is_leaf()]
    # Remove all children from the list
    to_remove = [child for child in children_name if child in nodes_name]
    nodes_name = [name for name in nodes_name if name not in to_remove]
    # Check if a parent exists, otherwise it is a root and it is appended to
    # the list
    if not hasattr(node_ref.up, "name"):
        nodes_name.append(node_ref.name)
    # Check if the parent of the node is not in the list, and then append it
    elif node_ref.up.name not in nodes_name:
        nodes_name.append(node_ref.name)
    return nodes_name


def inter_node_complete(list_taxid, tree_topo, rfg):
    """
    For each leaf, check if a common node exists with other leaves given by
    user. Then, remove leaves under node and do the intersection between
    nodes. Return this dictionary and the list of leaves remaining
    """
    nodes_checked = []
    for leaf_id in list_taxid:
        if traversing_tree(tree_topo.get_leaves_by_name(leaf_id)[0].up, list_taxid):
            # Check this node is not a subnode of a node in the list
            nodes_checked = issubnode(tree_topo.get_leaves_by_name(leaf_id)[0].up, nodes_checked)

    leaves_to_rm = []
    # Keep name of leaves under checked nodes
    for name_node in nodes_checked:
        current_node = tree_topo.search_nodes(name=name_node)[0]
        leaves_to_rm += [leaf for leaf in current_node.iter_leaf_names()]
    # Only keep leaves that are not under checked nodes
    list_taxid = [taxid for taxid in list_taxid if taxid not in leaves_to_rm]
    return nodes_checked, list_taxid



def inter_node_in(nodes_checked, rfg):
    """
    Definition
    """
    path_nodes_checked = [rfg + "/node/inter/" + node + ".p" for node in nodes_checked]
    # Return the intersection of checked nodes
    if path_nodes_checked:
        dic_inter_nodes = inter.inter_nodes(pickle.load(open(path_nodes_checked[0], "rb"))["data"],
                                            path_nodes_checked[1:])
        return dic_inter_nodes
    return {}


def union_node_notin(nodes_checked, dict_org, rfg):
    """
    Definition
    """
    path_nodes_checked = [rfg + "/node/union/" + node + ".p" for node in nodes_checked]
    # Return the union of checked nodes
    if path_nodes_checked:
        dic_union_nodes = inter.union_dic(path_nodes_checked, {}, dict_org, False, rfg)
        return dic_union_nodes
    return {}


def find_node_complete(dict_org, list_taxid_in, rfg):
    """
    Create the topology tree and find common node for included and excluded
    organism
    """
    tree_topo = create_topo_tree(dict_org)

    list_node_in, list_taxid_in = inter_node_complete(list_taxid_in, tree_topo, rfg)
    dic_node_in = inter_node_in(list_node_in, rfg)
    # list_node_notin, list_taxid_notin = inter_node_complete(list_taxid_notin, tree_topo, rfg)
    # dic_node_notin = union_node_notin(list_node_notin, dict_org, rfg)

    return dic_node_in, list_taxid_in


def soustract_node(dic_node_in, dic_node_notin):
    """
    Definition
    """
    if dic_node_in and dic_node_notin:
        keys_in = set(dic_node_in.keys())
        keys_notin = set(dic_node_notin.keys())
        common_keys = list(keys_in & keys_notin)
        print("NOMBRE de clef communes " + str(len(common_keys)))
        for sgrna in common_keys:
            del dic_node_in[sgrna]
        return dic_node_in, True
    elif dic_node_in:
        return dic_node_in, True
    else:
        return dic_node_notin, False



if __name__ == '__main__':
    PARAM = args_gestion()
    DICT_ORG = json.load(open(PARAM.rfg + '/genome_ref_taxid.json', 'r'))
    LIST_TAXID_IN, LIST_TAXID_NOTIN = setup_application(PARAM, DICT_ORG)
    DIC_NODE_IN, DIC_NODE_NOTIN, LIST_TAXID_IN, LIST_TAXID_NOTIN = find_node_complete(DICT_ORG,
                                                                                      LIST_TAXID_IN,
                                                                                      LIST_TAXID_NOTIN,
                                                                                      PARAM.rfg)
    DIC_JENESAISPASQUOI = soustract_node(DIC_NODE_IN, DIC_NODE_NOTIN)
    print(len(DIC_JENESAISPASQUOI))
# Exemple commande
# ./scan_tree.py -rfg ../reference_genomes_pickle -gi "Streptosporangium roseum DSM 43021 GCF_000024865.1&Catenulispora acidiphila DSM 44928 GCF_000024025.1&Streptomyces violaceusniger Tu 4113 GCF_000147815.2&Streptomyces bingchenggensis BCW-1 GCF_000092385.1&Archangium gephyra GCF_001027285.1" -gni ""
