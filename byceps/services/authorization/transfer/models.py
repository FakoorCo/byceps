"""
byceps.services.authorization.transfer.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from dataclasses import dataclass
from typing import NewType


PermissionID = NewType('PermissionID', str)


RoleID = NewType('RoleID', str)


@dataclass(frozen=True)
class Permission:
    id: PermissionID
    title: str


@dataclass(frozen=True)
class Role:
    id: RoleID
    title: str
