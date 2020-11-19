from dedoc.config import get_config

config = get_config()


def get_command_keep_models():
    """
    Ignore some private models in swagger api documentations
    """
    none_display = "{display: none !important}"
    discription = "API <style> " + ' '.join(["div#model-refTreeNode{depth} {none_display}"
                                            .format(depth=i, none_display=none_display)
                                             for i in range(config['recursion_deep_subparagraphs'])]) \
                  + ' '.join(["div#model-refParsedDocument{depth} {none_display}"
                             .format(depth=i, none_display=none_display)
                              for i in range(config['recursion_deep_attachments'])]) \
                  + " div#model-others_ParsedDocument {none_display} ".format(none_display=none_display) \
                  + " div#model-others_TreeNode {none_display}".format(none_display=none_display)\
                  + " div#model-Predicts {none_display}".format(none_display=none_display)\
                  + " </style>"

    return discription
