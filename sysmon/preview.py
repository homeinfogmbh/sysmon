"""Administrative token preview generation."""

from his import Account
from hwdb import Deployment
from previewlib import DeploymentPreviewToken
from termacls import get_administerable_deployments


__all__ = ["generate_preview_token"]


def generate_preview_token(deployment: int, account: Account) -> DeploymentPreviewToken:
    """Generate a deployment preview token by
    the deployment id for the given account.
    """

    return _generate_preview_token(
        get_administerable_deployments(account).where(Deployment.id == deployment).get()
    )


def _generate_preview_token(deployment: Deployment) -> DeploymentPreviewToken:
    """Generate a deployment preview token."""

    try:
        return DeploymentPreviewToken.get(DeploymentPreviewToken.obj == deployment)
    except DeploymentPreviewToken.DoesNotExist:
        token = DeploymentPreviewToken(obj=deployment)
        token.save()
        return token
