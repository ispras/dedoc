from collections import defaultdict
from dataclasses import dataclass

from tdm import DefaultDocumentFactory, TalismanDocument
from tdm.abstract.datamodel import AbstractNode, AbstractNodeLink
from tdm.datamodel.nodes import TextNode

from dedoc_future.abstract.blob_ref import NodeId


@dataclass(frozen=True)
class ContainerSpec:
    nodes: frozenset[type[AbstractNode]] = frozenset()
    include_parents: bool = False
    include_children: bool = False
    links: frozenset[type[AbstractNodeLink]] = frozenset()
    whole_document: bool = False

    def build(self, source: TalismanDocument, node_ids: set[NodeId] | None = None) -> TalismanDocument:
        if self.whole_document:
            return source

        root = TextNode("")
        new_container = DefaultDocumentFactory().create_document().with_main_root(root, update=True)
        structure = defaultdict(list)

        if node_ids is not None:
            ids = node_ids
        else:
            ids: set[NodeId] = set()
            for node_type in self.nodes:
                ids |= {n.id for n in source.get_nodes(node_type)}

        if self.include_parents:
            for node_id in ids:
                node_parent = source.parent(node_id)
                if node_parent is not None:
                    ids.add(node_parent.id)
                    structure[node_parent.id].append(node_id)
                    structure[root.id].append(node_parent.id)
                else:
                    structure[root.id].append(node_id)
        else:
            structure[root.id].extend(ids)

        if self.include_children:
            for node_id in list(ids):
                child_ids = {c.id for c in source.child_nodes(node_id)}
                ids |= child_ids
                structure[node_id].extend(child_ids)

        links = []
        for link_type in self.links:
            for link in source.get_node_links(link_type):
                if link.source.node.id in ids or link.target.node.id in ids:
                    ids |= {link.source.node.id, link.target.node.id}
                    links.append(link)

        new_container = new_container.with_nodes([source.id2node[i] for i in ids]).with_structure(structure)
        if self.links:
            new_container = new_container.with_node_links(links)
        return new_container
