# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Matthias Klumpp <mak@debian.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public  License
# as published by the Free Software Foundation; either version
# 3.0 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program.

import os
from sqlalchemy import Column, Table, types
from sqlalchemy.ext.mutable import Mutable
from flask import current_app

from ..extensions import db
from ..utils import make_dir, get_current_time, STRING_LEN

from .constants import RepoFlag, PackageKind

class Repository(db.Model):

    __tablename__ = 'repositories'

    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(STRING_LEN), nullable=False)
    created_time = Column(db.DateTime, default=get_current_time)
    toplevel = Column(db.Boolean, default=False)
    flag = Column(db.Integer, default=RepoFlag.NONE)

    user_id = Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", uselist=False, backref="repositories")


    @property
    def root_dir(self):
        main_root = current_app.config['REPOS_ROOT']
        path = None
        if self.toplevel:
            path = os.path.join(main_root, self.name)
        else:
            path = os.path.join(main_root, "users", self.user.name, self.name)
        make_dir(path)
        return path

    def data_url_for (self, filename):
        return "%s/%s/%s" % (current_app.config['REPOS_ROOT_URL'], self.name, filename)


class RepoPermission(db.Model):

    __tablename__ = 'repo_permissions'

    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", uselist=False, backref="repo_permissions")
    pkgname = Column(db.String(), nullable=False)
    repo_id = Column(db.Integer, db.ForeignKey("repositories.id"))
    repository = db.relationship("Repository", uselist=False, backref="repo_permissions")
    details = Column(db.String(), nullable=True)


class Category(db.Model):

    __tablename__ = 'categories'

    id = Column(db.Integer, primary_key=True)
    idname = Column(db.String(), nullable=False)
    name = Column(db.String(), nullable=False)
    description = Column(db.String(), nullable=False)

    parent_id = Column(db.Integer, db.ForeignKey("categories.id"))
    parent = db.relationship("Category", remote_side=[id], backref="subcategories")

    def is_toplevel(self):
        return not self.subcategories


class Package(db.Model):

    __tablename__ = 'packages'

    id = Column(db.Integer, primary_key=True)
    name = Column(db.String(), nullable=False)
    version = Column(db.String(), nullable=False)
    fname = Column(db.String(), nullable=False)
    architecture = Column(db.String(), nullable=False)
    kind = Column(db.Integer, default=PackageKind.COMMON)

    dependencies = Column(db.String(), nullable=True)

    created_time = Column(db.DateTime, default=get_current_time)

    sha256sum = Column(db.String(), nullable=False)

    repository_id = Column(db.Integer, db.ForeignKey("repositories.id"))
    repository = db.relationship("Repository", uselist=False, backref="packages")

    component_id = Column(db.Integer, db.ForeignKey("components.id"))
    component = db.relationship("Component", backref="packages")

component_categories = Table('component_categories', db.Model.metadata,
     Column('component_id', db.Integer, db.ForeignKey('components.id')),
     Column('category_id', db.Integer, db.ForeignKey('categories.id'))
)


class Component(db.Model):

    __tablename__ = 'components'

    id = Column(db.Integer, primary_key=True)
    cid = Column(db.String(), nullable=False)
    kind = Column(db.String(), nullable=False)
    sdk = Column(db.Boolean, default=False)

    user_id = Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", uselist=False, backref="components")

    name = Column(db.String(), nullable=False)
    summary = Column(db.String(), nullable=False)
    description = Column(db.String(), nullable=False)

    developer_name = Column(db.String(), nullable=True)
    url = Column(db.String(), nullable=True)

    xml = Column(db.String(), nullable=False)

    repository_id = Column(db.Integer, db.ForeignKey("repositories.id"))
    repository = db.relationship("Repository", uselist=False, backref="components")

    categories = db.relationship('Category', secondary=component_categories, backref='components')
