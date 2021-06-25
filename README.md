# Django Database Warden: **WIP**

Goal: A django application that takes advantage of Postgresql [row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) to manage what queries & records users can interact with within a database.

TODOs:

- Implement RLS functionality
    - Add ability to mark models for RLS enabling
- Create test app to see how well it works ??
- Add a way to optionally grant & revoke connect priveleges for created users
- **Low priority; Probably won't do** Add ability to modify created permissions & users ? _Might not be the best idea perhaps ?_

Features so far:

- Able to create & delete database users & permissions
    - On create & delete functionality actually performs changes on the database


Interesting things discovered while working on this:

- RLS Performance is a bit slow in versions of Postgres before v10. Sources https://stackoverflow.com/a/45213705, https://github.com/postgres/postgres/commit/215b43cdc8d6b4a1700886a39df1ee735cb0274d