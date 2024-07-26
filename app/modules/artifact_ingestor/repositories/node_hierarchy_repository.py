from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.modules.artifact_ingestor.models.node_hierarchy import NodeHierarchy

Base = declarative_base()


# Define the repository class
class NodeHierarchyRepo:
    def __init__(self, session: Session):
        self.session = session

    def save(self, node_hierarchy: NodeHierarchy) -> NodeHierarchy:
        self.session.add(node_hierarchy)
        return node_hierarchy

    def find_by_id(self, node_hierarchy_composite_key):
        try:
            return (
                self.session.query(NodeHierarchy)
                .filter_by(
                    parent_node_id=node_hierarchy_composite_key.parent_node_id,
                    child_node_id=node_hierarchy_composite_key.child_node_id,
                )
                .one()
            )
        except NoResultFound:
            return None

    def count_by_child_node(self, node_id):
        return (
            self.session.query(func.count(NodeHierarchy))
            .filter(
                (NodeHierarchy.child_node_id == node_id)
                | (NodeHierarchy.parent_node_id == node_id)
            )
            .scalar()
        )

    def find_all_parent_ids_by_child_id(self, child_id):
        return (
            self.session.query(NodeHierarchy.parent_node_id)
            .filter(NodeHierarchy.child_node_id == child_id)
            .all()
        )

    def add(self, node_hierarchy):
        self.session.add(node_hierarchy)
        self.session.commit()

    def remove(self, node_hierarchy_composite_key):
        node_hierarchy = self.find_by_id(node_hierarchy_composite_key)
        if node_hierarchy:
            self.session.delete(node_hierarchy)
            self.session.commit()
