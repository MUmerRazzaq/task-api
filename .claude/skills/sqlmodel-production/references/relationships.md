# SQLModel Relationships

## One-to-Many Relationship

The most common relationship pattern. One parent has many children.

```python
from sqlmodel import Field, Relationship, SQLModel

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    # One team has many heroes
    heroes: list["Hero"] = Relationship(back_populates="team")


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

    # Foreign key - ALWAYS index for performance
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)

    # Many heroes belong to one team
    team: Team | None = Relationship(back_populates="heroes")
```

### Creating Related Objects

```python
# Method 1: Set relationship object directly
with Session(engine) as session:
    team = Team(name="Preventers", headquarters="Sharp Tower")
    hero = Hero(name="Spider-Boy", secret_name="Pedro", team=team)
    session.add(hero)  # Team is added automatically
    session.commit()

# Method 2: Set foreign key after parent commit
with Session(engine) as session:
    team = Team(name="Preventers", headquarters="Sharp Tower")
    session.add(team)
    session.commit()  # team.id now available

    hero = Hero(name="Spider-Boy", secret_name="Pedro", team_id=team.id)
    session.add(hero)
    session.commit()

# Method 3: Add to parent's collection
with Session(engine) as session:
    team = Team(
        name="Preventers",
        headquarters="Sharp Tower",
        heroes=[
            Hero(name="Spider-Boy", secret_name="Pedro"),
            Hero(name="Rusty-Man", secret_name="Tommy", age=48),
        ]
    )
    session.add(team)
    session.commit()
```

---

## Many-to-Many Relationship

Use a link table (association table) when entities have multiple connections.

### Basic Many-to-Many

```python
from sqlmodel import Field, Relationship, SQLModel

# Link table - connects heroes and teams
class HeroTeamLink(SQLModel, table=True):
    team_id: int | None = Field(default=None, foreign_key="team.id", primary_key=True)
    hero_id: int | None = Field(default=None, foreign_key="hero.id", primary_key=True)


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    heroes: list["Hero"] = Relationship(back_populates="teams", link_model=HeroTeamLink)


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

    teams: list[Team] = Relationship(back_populates="heroes", link_model=HeroTeamLink)
```

### Many-to-Many with Extra Data on Link

When you need additional fields on the relationship itself:

```python
class HeroTeamLink(SQLModel, table=True):
    team_id: int | None = Field(default=None, foreign_key="team.id", primary_key=True)
    hero_id: int | None = Field(default=None, foreign_key="hero.id", primary_key=True)

    # Extra data on the relationship
    is_training: bool = False
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    role: str = Field(default="member")

    # Relationships to access link from both sides
    team: "Team" = Relationship(back_populates="hero_links")
    hero: "Hero" = Relationship(back_populates="team_links")


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str

    # Access links (with extra data)
    hero_links: list[HeroTeamLink] = Relationship(back_populates="team")


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str

    # Access links (with extra data)
    team_links: list[HeroTeamLink] = Relationship(back_populates="hero")
```

### Creating Many-to-Many with Extra Data

```python
with Session(engine) as session:
    team = Team(name="Preventers", headquarters="Sharp Tower")
    hero = Hero(name="Spider-Boy", secret_name="Pedro")

    # Create link with extra data
    link = HeroTeamLink(team=team, hero=hero, is_training=True, role="trainee")

    session.add(link)  # Adds team and hero automatically
    session.commit()

    # Access extra data
    for link in team.hero_links:
        print(f"{link.hero.name} - Training: {link.is_training}, Role: {link.role}")
```

---

## One-to-One Relationship

Use `uselist=False` in `sa_relationship_kwargs`:

```python
from sqlmodel import Field, Relationship, SQLModel

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # One user has one profile
    profile: "Profile | None" = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )


class Profile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    bio: str
    avatar_url: str | None = None

    user_id: int = Field(foreign_key="user.id", unique=True)  # unique=True enforces 1:1
    user: User = Relationship(back_populates="profile")
```

---

## Self-Referential Relationship

For hierarchical data (tree structures):

```python
class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # Self-reference for parent
    parent_id: int | None = Field(default=None, foreign_key="category.id", index=True)

    # Parent relationship
    parent: "Category | None" = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Category.id"}
    )

    # Children relationship
    children: list["Category"] = Relationship(back_populates="parent")
```

---

## Cascade Deletes

Configure what happens when parent is deleted:

```python
class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    heroes: list["Hero"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)
    team: Team | None = Relationship(back_populates="heroes")
```

**Cascade options:**
- `"all, delete-orphan"` - Delete children when parent deleted
- `"save-update, merge"` - Default, no cascade delete
- `"delete"` - Delete children but allow orphans

---

## Relationship Response Models

```python
# Team response with nested heroes
class HeroInTeam(SQLModel):
    id: int
    name: str

class TeamPublicWithHeroes(SQLModel):
    id: int
    name: str
    headquarters: str
    heroes: list[HeroInTeam] = []


# Hero response with nested team
class TeamInHero(SQLModel):
    id: int
    name: str

class HeroPublicWithTeam(SQLModel):
    id: int
    name: str
    secret_name: str
    team: TeamInHero | None = None
```
