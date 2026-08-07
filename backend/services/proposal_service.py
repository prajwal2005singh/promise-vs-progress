from sqlalchemy.orm import Session

from models.proposal import ProjectProposal
from models.project import Project

from schemas.proposal import ProposalCreate


def create_proposal(
    db: Session,
    proposal: ProposalCreate,
    user_id: int
):

    db_proposal = ProjectProposal(
        **proposal.model_dump(),
        submitted_by=user_id
    )

    db.add(db_proposal)

    db.commit()

    db.refresh(db_proposal)

    return db_proposal


def get_all_proposals(db: Session):

    return db.query(ProjectProposal).all()


def get_proposal_by_id(
    db: Session,
    proposal_id: int
):

    return (
        db.query(ProjectProposal)
        .filter(ProjectProposal.id == proposal_id)
        .first()
    )


def approve_proposal(
    db: Session,
    proposal_id: int,
    admin_id: int
):

    proposal = get_proposal_by_id(
        db,
        proposal_id
    )

    if proposal is None:
        return None

    if proposal.status != "PENDING":
        return None

    project = Project(

        name=proposal.name,

        description=proposal.description,

        category=proposal.category,

        location_name=proposal.location_name,

        latitude=proposal.latitude,

        longitude=proposal.longitude,

        budget=proposal.budget,

        department="Citizen Proposal",

        created_by=admin_id
    )

    db.add(project)

    db.commit()

    db.refresh(project)

    proposal.status = "APPROVED"

    proposal.reviewed_by = admin_id

    proposal.created_project_id = project.id

    db.commit()

    db.refresh(proposal)

    return proposal


def reject_proposal(
    db: Session,
    proposal_id: int,
    admin_id: int,
    reason: str
):

    proposal = get_proposal_by_id(
        db,
        proposal_id
    )

    if proposal is None:
        return None

    proposal.status = "REJECTED"

    proposal.reviewed_by = admin_id

    proposal.review_comment = reason

    db.commit()

    db.refresh(proposal)

    return proposal