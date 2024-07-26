from sqlalchemy.orm import Session
from sqlalchemy import and_
from common.models.artifacts import Artifacts


class ArtifactRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, artifact: Artifacts) -> Artifacts:
        self.session.add(artifact)
        return artifact

    def find_by_id(self, artifact_id):
        return self.session.query(Artifacts).filter(Artifacts.id == artifact_id).first()

    def find_by_filters_all(
        self,
        tenant_id,
        context=None,
        domain=None,
        sub_domain=None,
        region=None,
        country=None,
        state=None,
        city=None,
        category=None,
        type=None,
        artifact_ids=None,
    ):
        query = self.session.query(Artifacts).filter(Artifacts.tenant_id == tenant_id)

        if context:
            query = query.filter(Artifacts.context.in_(context))
        if domain:
            query = query.filter(Artifacts.domain.in_(domain))
        if sub_domain:
            query = query.filter(Artifacts.sub_domain.in_(sub_domain))
        if region:
            query = query.filter(Artifacts.region.in_(region))
        if country:
            query = query.filter(Artifacts.country.in_(country))
        if state:
            query = query.filter(Artifacts.state.in_(state))
        if city:
            query = query.filter(Artifacts.city.in_(city))
        if category:
            query = query.filter(Artifacts.category_id.in_(category))
        if type:
            query = query.filter(Artifacts.type_id.in_(type))
        if artifact_ids:
            query = query.filter(Artifacts.id.in_(artifact_ids))

        return query.all()

    def find_by_filters_all_and_enabled(
        self,
        tenant_id,
        context=None,
        domain=None,
        sub_domain=None,
        region=None,
        country=None,
        state=None,
        city=None,
        category=None,
        type=None,
        artifact_ids=None,
    ):
        query = self.session.query(Artifacts).filter(
            and_(Artifacts.tenant_id == tenant_id, Artifacts.enabled.is_(True))
        )

        if context:
            query = query.filter(Artifacts.context.in_(context))
        if domain:
            query = query.filter(Artifacts.domain.in_(domain))
        if sub_domain:
            query = query.filter(Artifacts.sub_domain.in_(sub_domain))
        if region:
            query = query.filter(Artifacts.region.in_(region))
        if country:
            query = query.filter(Artifacts.country.in_(country))
        if state:
            query = query.filter(Artifacts.state.in_(state))
        if city:
            query = query.filter(Artifacts.city.in_(city))
        if category:
            query = query.filter(Artifacts.category_id.in_(category))
        if type:
            query = query.filter(Artifacts.type_id.in_(type))
        if artifact_ids:
            query = query.filter(Artifacts.id.in_(artifact_ids))

        return query.all()

    def distinct_context(self):
        return self.session.query(Artifacts.context).distinct().all()

    def find_distinct_categories_by_context_and_tenant_id(self, context, tenant_id):
        return (
            self.session.query(Artifacts.category_id)
            .filter(Artifacts.context == context, Artifacts.tenant_id == tenant_id)
            .distinct()
            .all()
        )

    def find_distinct_geographies_by_context_and_tenant_id(self, context, tenant_id):
        return (
            self.session.query(
                Artifacts.region, Artifacts.country, Artifacts.state, Artifacts.city
            )
            .filter(Artifacts.context == context, Artifacts.tenant_id == tenant_id)
            .distinct()
            .all()
        )

    def find_distinct_artifact_types_by_context_and_tenant_id(self, context, tenant_id):
        return (
            self.session.query(Artifacts.type_id)
            .filter(Artifacts.context == context, Artifacts.tenant_id == tenant_id)
            .distinct()
            .all()
        )

    def find_distinct_tags_by_context_and_tenant_id(self, context, tenant_id):
        return (
            self.session.query(Artifacts.tags)
            .filter(Artifacts.context == context, Artifacts.tenant_id == tenant_id)
            .distinct()
            .all()
        )

    def count_by_source_link_and_tenant_id(self, source_link, tenant_id):
        return (
            self.session.query(Artifacts)
            .filter(
                Artifacts.source_link == source_link, Artifacts.tenant_id == tenant_id
            )
            .count()
        )

    def count_by_name_and_tenant_id(self, name, tenant_id):
        return (
            self.session.query(Artifacts)
            .filter(Artifacts.name == name, Artifacts.tenant_id == tenant_id)
            .count()
        )

    def save_and_flush(self, artifact: Artifacts) -> Artifacts:
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def update_artifact_location(self, artifact_id, location):
        artifact = (
            self.session.query(Artifacts).filter(Artifacts.id == artifact_id).first()
        )
        if artifact:
            artifact.uploaded_location = location
            self.session.commit()

    def enable_artifacts(self, artifact_ids, enabled):
        self.session.query(Artifacts).filter(Artifacts.id.in_(artifact_ids)).update(
            {Artifacts.enabled: enabled}
        )
        self.session.commit()

    def enable_all_artifacts(self, enabled):
        self.session.query(Artifacts).update({Artifacts.enabled: enabled})
        self.session.commit()

    def find_by_name(self, name, tenant_id):
        return (
            self.session.query(Artifacts.id)
            .filter(Artifacts.name.like(f"%{name}%"), Artifacts.tenant_id == tenant_id)
            .all()
        )
