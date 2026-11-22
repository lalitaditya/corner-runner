"""Typed records for mechfight/1. Entries follow the wire schema and use its zero defaults."""

import math


class Hello:
    __slots__ = ("Type", "Protocol", "Slot", "Seed", "Map", "Config")

    def __init__(self, Type=None, Protocol=None, Slot=None, Seed=None, Map=None, Config=None):
        self.Type = "" if Type is None else Type
        self.Protocol = "" if Protocol is None else Protocol
        self.Slot = 0 if Slot is None else Slot
        self.Seed = 0 if Seed is None else Seed
        self.Map = HelloMap() if Map is None else Map
        self.Config = Config() if Config is None else Config


class HelloMap:
    __slots__ = ("Dir", "Files")

    def __init__(self, Dir=None, Files=None):
        self.Dir = "" if Dir is None else Dir
        self.Files = [] if Files is None else Files


class ZonePhase:
    __slots__ = ("HoldS", "ShrinkS", "Radius", "Dps")

    def __init__(self, HoldS=None, ShrinkS=None, Radius=None, Dps=None):
        self.HoldS = 0.0 if HoldS is None else HoldS
        self.ShrinkS = 0.0 if ShrinkS is None else ShrinkS
        self.Radius = 0.0 if Radius is None else Radius
        self.Dps = 0.0 if Dps is None else Dps


class Effect:
    __slots__ = ("Path", "Mul", "Add")

    def __init__(self, Path=None, Mul=None, Add=None):
        self.Path = "" if Path is None else Path
        self.Mul = Mul
        self.Add = Add


class UpgradeDef:
    __slots__ = ("ID", "Name", "Desc", "Requires", "Max", "Effects")

    def __init__(self, ID=None, Name=None, Desc=None, Requires=None, Max=None, Effects=None):
        self.ID = "" if ID is None else ID
        self.Name = "" if Name is None else Name
        self.Desc = "" if Desc is None else Desc
        self.Requires = "" if Requires is None else Requires
        self.Max = 0 if Max is None else Max
        self.Effects = [] if Effects is None else Effects


class Config:
    __slots__ = (
        "Match",
        "Bot",
        "Mech",
        "Vision",
        "Sound",
        "Weapons",
        "Projectile",
        "Cubes",
        "Crates",
        "Loot",
        "Npc",
        "Drops",
        "Zone",
        "Replay",
        "Debug",
        "Upgrades",
    )

    def __init__(
        self,
        Match=None,
        Bot=None,
        Mech=None,
        Vision=None,
        Sound=None,
        Weapons=None,
        Projectile=None,
        Cubes=None,
        Crates=None,
        Loot=None,
        Npc=None,
        Drops=None,
        Zone=None,
        Replay=None,
        Debug=None,
        Upgrades=None,
    ):
        self.Match = {} if Match is None else Match
        self.Bot = {} if Bot is None else Bot
        self.Mech = {} if Mech is None else Mech
        self.Vision = ConfigVision() if Vision is None else Vision
        self.Sound = ConfigSound() if Sound is None else Sound
        self.Weapons = {} if Weapons is None else Weapons
        self.Projectile = {} if Projectile is None else Projectile
        self.Cubes = ConfigCubes() if Cubes is None else Cubes
        self.Crates = {} if Crates is None else Crates
        self.Loot = ConfigLoot() if Loot is None else Loot
        self.Npc = {} if Npc is None else Npc
        self.Drops = Drops
        self.Zone = ConfigZone() if Zone is None else Zone
        self.Replay = {} if Replay is None else Replay
        self.Debug = {} if Debug is None else Debug
        self.Upgrades = [] if Upgrades is None else Upgrades


class ConfigVision:
    __slots__ = ("Range", "FovDeg", "NearRange", "CanopyBlocks", "ShowEnemyHP", "MemoryS")

    def __init__(
        self, Range=None, FovDeg=None, NearRange=None, CanopyBlocks=None, ShowEnemyHP=None, MemoryS=None
    ):
        self.Range = 0.0 if Range is None else Range
        self.FovDeg = 0.0 if FovDeg is None else FovDeg
        self.NearRange = 0.0 if NearRange is None else NearRange
        self.CanopyBlocks = False if CanopyBlocks is None else CanopyBlocks
        self.ShowEnemyHP = False if ShowEnemyHP is None else ShowEnemyHP
        self.MemoryS = 0.0 if MemoryS is None else MemoryS


class ConfigSound:
    __slots__ = ("BearingNoiseDeg", "Near", "Mid", "StepSpeed", "StepEvery", "Range")

    def __init__(self, BearingNoiseDeg=None, Near=None, Mid=None, StepSpeed=None, StepEvery=None, Range=None):
        self.BearingNoiseDeg = 0.0 if BearingNoiseDeg is None else BearingNoiseDeg
        self.Near = 0.0 if Near is None else Near
        self.Mid = 0.0 if Mid is None else Mid
        self.StepSpeed = 0.0 if StepSpeed is None else StepSpeed
        self.StepEvery = 0.0 if StepEvery is None else StepEvery
        self.Range = {} if Range is None else Range


class ConfigCubes:
    __slots__ = (
        "PickupRadius",
        "HPPerCube",
        "DamagePerCube",
        "StatCap",
        "DeathDropExtra",
        "SizePerCube",
        "UpgradeThresholds",
    )

    def __init__(
        self,
        PickupRadius=None,
        HPPerCube=None,
        DamagePerCube=None,
        StatCap=None,
        DeathDropExtra=None,
        SizePerCube=None,
        UpgradeThresholds=None,
    ):
        self.PickupRadius = 0.0 if PickupRadius is None else PickupRadius
        self.HPPerCube = 0.0 if HPPerCube is None else HPPerCube
        self.DamagePerCube = 0.0 if DamagePerCube is None else DamagePerCube
        self.StatCap = 0.0 if StatCap is None else StatCap
        self.DeathDropExtra = 0.0 if DeathDropExtra is None else DeathDropExtra
        self.SizePerCube = 0.0 if SizePerCube is None else SizePerCube
        self.UpgradeThresholds = [] if UpgradeThresholds is None else UpgradeThresholds


class ConfigLoot:
    __slots__ = (
        "PickupRadius",
        "EquipS",
        "FloorCount",
        "FloorRoofFraction",
        "CrateWeaponChance",
        "DeathDrop",
        "Weights",
    )

    def __init__(
        self,
        PickupRadius=None,
        EquipS=None,
        FloorCount=None,
        FloorRoofFraction=None,
        CrateWeaponChance=None,
        DeathDrop=None,
        Weights=None,
    ):
        self.PickupRadius = 0.0 if PickupRadius is None else PickupRadius
        self.EquipS = 0.0 if EquipS is None else EquipS
        self.FloorCount = 0.0 if FloorCount is None else FloorCount
        self.FloorRoofFraction = 0.0 if FloorRoofFraction is None else FloorRoofFraction
        self.CrateWeaponChance = 0.0 if CrateWeaponChance is None else CrateWeaponChance
        self.DeathDrop = 0.0 if DeathDrop is None else DeathDrop
        self.Weights = {} if Weights is None else Weights


class ConfigDrops:
    __slots__ = ("Times", "FallS", "Radius", "CaptureS", "Cubes", "Repair", "Spread")

    def __init__(
        self, Times=None, FallS=None, Radius=None, CaptureS=None, Cubes=None, Repair=None, Spread=None
    ):
        self.Times = [] if Times is None else Times
        self.FallS = 0.0 if FallS is None else FallS
        self.Radius = 0.0 if Radius is None else Radius
        self.CaptureS = 0.0 if CaptureS is None else CaptureS
        self.Cubes = 0.0 if Cubes is None else Cubes
        self.Repair = 0.0 if Repair is None else Repair
        self.Spread = 0.0 if Spread is None else Spread


class ConfigZone:
    __slots__ = ("StartCenter", "StartRadius", "Phases")

    def __init__(self, StartCenter=None, StartRadius=None, Phases=None):
        self.StartCenter = [] if StartCenter is None else StartCenter
        self.StartRadius = 0.0 if StartRadius is None else StartRadius
        self.Phases = [] if Phases is None else Phases


class WeaponObs:
    __slots__ = ("Kind", "Cooldown", "Ammo", "Reload", "Charge", "Stats")

    def __init__(self, Kind=None, Cooldown=None, Ammo=None, Reload=None, Charge=None, Stats=None):
        self.Kind = "" if Kind is None else Kind
        self.Cooldown = 0.0 if Cooldown is None else Cooldown
        self.Ammo = 0.0 if Ammo is None else Ammo
        self.Reload = 0.0 if Reload is None else Reload
        self.Charge = 0.0 if Charge is None else Charge
        self.Stats = Stats


class SelfObs:
    __slots__ = (
        "ID",
        "Pos",
        "Vel",
        "Aim",
        "HP",
        "MaxHP",
        "Energy",
        "MaxEnergy",
        "Grounded",
        "Cubes",
        "Upgrades",
        "InZone",
        "Weapons",
        "Stats",
    )

    def __init__(
        self,
        ID=None,
        Pos=None,
        Vel=None,
        Aim=None,
        HP=None,
        MaxHP=None,
        Energy=None,
        MaxEnergy=None,
        Grounded=None,
        Cubes=None,
        Upgrades=None,
        InZone=None,
        Weapons=None,
        Stats=None,
    ):
        self.ID = 0 if ID is None else ID
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos
        self.Vel = [0.0, 0.0, 0.0] if Vel is None else Vel
        self.Aim = [0.0, 0.0] if Aim is None else Aim
        self.HP = 0.0 if HP is None else HP
        self.MaxHP = 0.0 if MaxHP is None else MaxHP
        self.Energy = 0.0 if Energy is None else Energy
        self.MaxEnergy = 0.0 if MaxEnergy is None else MaxEnergy
        self.Grounded = False if Grounded is None else Grounded
        self.Cubes = 0 if Cubes is None else Cubes
        self.Upgrades = [] if Upgrades is None else Upgrades
        self.InZone = False if InZone is None else InZone
        self.Weapons = [] if Weapons is None else Weapons
        self.Stats = {} if Stats is None else Stats


class ActorObs:
    __slots__ = ("ID", "Kind", "Pos", "Vel", "Aim", "HP", "MaxHP", "Cubes", "Weapons", "Charging")

    def __init__(
        self,
        ID=None,
        Kind=None,
        Pos=None,
        Vel=None,
        Aim=None,
        HP=None,
        MaxHP=None,
        Cubes=None,
        Weapons=None,
        Charging=None,
    ):
        self.ID = 0 if ID is None else ID
        self.Kind = "" if Kind is None else Kind
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos
        self.Vel = [0.0, 0.0, 0.0] if Vel is None else Vel
        self.Aim = [0.0, 0.0] if Aim is None else Aim
        self.HP = 0.0 if HP is None else HP
        self.MaxHP = 0.0 if MaxHP is None else MaxHP
        self.Cubes = 0 if Cubes is None else Cubes
        self.Weapons = [] if Weapons is None else Weapons
        self.Charging = False if Charging is None else Charging


class ProjectileObs:
    __slots__ = ("ID", "Kind", "Pos", "Vel")

    def __init__(self, ID=None, Kind=None, Pos=None, Vel=None):
        self.ID = 0 if ID is None else ID
        self.Kind = "" if Kind is None else Kind
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos
        self.Vel = [0.0, 0.0, 0.0] if Vel is None else Vel


class ItemObs:
    __slots__ = ("ID", "Pos", "HP")

    def __init__(self, ID=None, Pos=None, HP=None):
        self.ID = 0 if ID is None else ID
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos
        self.HP = 0.0 if HP is None else HP


class PickupObs:
    __slots__ = ("ID", "Kind", "Pos")

    def __init__(self, ID=None, Kind=None, Pos=None):
        self.ID = 0 if ID is None else ID
        self.Kind = "" if Kind is None else Kind
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos


class SoundObs:
    __slots__ = ("Kind", "Bearing", "Dist", "Age")

    def __init__(self, Kind=None, Bearing=None, Dist=None, Age=None):
        self.Kind = "" if Kind is None else Kind
        self.Bearing = 0.0 if Bearing is None else Bearing
        self.Dist = "" if Dist is None else Dist
        self.Age = 0.0 if Age is None else Age


class BeamObs:
    __slots__ = ("By", "Kind", "Path", "Age")

    def __init__(self, By=None, Kind=None, Path=None, Age=None):
        self.By = 0 if By is None else By
        self.Kind = "" if Kind is None else Kind
        self.Path = [] if Path is None else Path
        self.Age = 0.0 if Age is None else Age


class Event:
    __slots__ = (
        "Type",
        "Amount",
        "Weapon",
        "Bearing",
        "By",
        "Rear",
        "Target",
        "Effect",
        "ID",
        "Cubes",
        "Kind",
        "Slot",
        "Reason",
    )

    def __init__(
        self,
        Type=None,
        Amount=None,
        Weapon=None,
        Bearing=None,
        By=None,
        Rear=None,
        Target=None,
        Effect=None,
        ID=None,
        Cubes=None,
        Kind=None,
        Slot=None,
        Reason=None,
    ):
        self.Type = "" if Type is None else Type
        self.Amount = 0.0 if Amount is None else Amount
        self.Weapon = "" if Weapon is None else Weapon
        self.Bearing = Bearing
        self.By = By
        self.Rear = False if Rear is None else Rear
        self.Target = 0 if Target is None else Target
        self.Effect = "" if Effect is None else Effect
        self.ID = IDValue() if ID is None else ID
        self.Cubes = 0 if Cubes is None else Cubes
        self.Kind = "" if Kind is None else Kind
        self.Slot = 0 if Slot is None else Slot
        self.Reason = "" if Reason is None else Reason


class IDValue:
    __slots__ = ("Num", "Str")

    def __init__(self, Num=None, Str=None):
        self.Num = 0 if Num is None else Num
        self.Str = "" if Str is None else Str


class DropObs:
    __slots__ = ("ID", "Pos", "Radius", "LandsIn", "CaptureS", "Progress", "Holder")

    def __init__(
        self, ID=None, Pos=None, Radius=None, LandsIn=None, CaptureS=None, Progress=None, Holder=None
    ):
        self.ID = 0 if ID is None else ID
        self.Pos = [0.0, 0.0, 0.0] if Pos is None else Pos
        self.Radius = 0.0 if Radius is None else Radius
        self.LandsIn = 0.0 if LandsIn is None else LandsIn
        self.CaptureS = 0.0 if CaptureS is None else CaptureS
        self.Progress = 0.0 if Progress is None else Progress
        self.Holder = Holder


class ZoneObs:
    __slots__ = ("Center", "Radius", "NextCenter", "NextRadius", "ShrinkStart", "ShrinkEnd", "Dps")

    def __init__(
        self,
        Center=None,
        Radius=None,
        NextCenter=None,
        NextRadius=None,
        ShrinkStart=None,
        ShrinkEnd=None,
        Dps=None,
    ):
        self.Center = [0.0, 0.0] if Center is None else Center
        self.Radius = 0.0 if Radius is None else Radius
        self.NextCenter = [0.0, 0.0] if NextCenter is None else NextCenter
        self.NextRadius = 0.0 if NextRadius is None else NextRadius
        self.ShrinkStart = 0.0 if ShrinkStart is None else ShrinkStart
        self.ShrinkEnd = 0.0 if ShrinkEnd is None else ShrinkEnd
        self.Dps = 0.0 if Dps is None else Dps


class OfferChoice:
    __slots__ = ("ID", "Name", "Desc")

    def __init__(self, ID=None, Name=None, Desc=None):
        self.ID = "" if ID is None else ID
        self.Name = "" if Name is None else Name
        self.Desc = "" if Desc is None else Desc


class Offer:
    __slots__ = ("ID", "Expires", "Choices")

    def __init__(self, ID=None, Expires=None, Choices=None):
        self.ID = 0 if ID is None else ID
        self.Expires = 0.0 if Expires is None else Expires
        self.Choices = [] if Choices is None else Choices


class Obs:
    __slots__ = (
        "Type",
        "Tick",
        "T",
        "Alive",
        "Self",
        "Mechs",
        "Projectiles",
        "Crates",
        "Cubes",
        "Pickups",
        "Sounds",
        "Beams",
        "Events",
        "Drops",
        "Zone",
        "Offer",
    )

    def __init__(
        self,
        Type=None,
        Tick=None,
        T=None,
        Alive=None,
        Self=None,
        Mechs=None,
        Projectiles=None,
        Crates=None,
        Cubes=None,
        Pickups=None,
        Sounds=None,
        Beams=None,
        Events=None,
        Drops=None,
        Zone=None,
        Offer=None,
    ):
        self.Type = "" if Type is None else Type
        self.Tick = 0 if Tick is None else Tick
        self.T = 0.0 if T is None else T
        self.Alive = 0 if Alive is None else Alive
        self.Self = SelfObs() if Self is None else Self
        self.Mechs = [] if Mechs is None else Mechs
        self.Projectiles = [] if Projectiles is None else Projectiles
        self.Crates = [] if Crates is None else Crates
        self.Cubes = [] if Cubes is None else Cubes
        self.Pickups = [] if Pickups is None else Pickups
        self.Sounds = [] if Sounds is None else Sounds
        self.Beams = [] if Beams is None else Beams
        self.Events = [] if Events is None else Events
        self.Drops = [] if Drops is None else Drops
        self.Zone = ZoneObs() if Zone is None else Zone
        self.Offer = Offer


class Action:
    __slots__ = (
        "Tick",
        "Move",
        "Boost",
        "Jump",
        "Aim",
        "HasAim",
        "Fire",
        "Reload",
        "Pick",
        "Take",
        "Drop",
        "Label",
    )

    def __init__(
        self,
        Tick=None,
        Move=None,
        Boost=None,
        Jump=None,
        Aim=None,
        HasAim=None,
        Fire=None,
        Reload=None,
        Pick=None,
        Take=None,
        Drop=None,
        Label=None,
    ):
        self.Tick = 0 if Tick is None else Tick
        self.Move = [0.0, 0.0] if Move is None else Move
        self.Boost = False if Boost is None else Boost
        self.Jump = False if Jump is None else Jump
        self.Aim = [0.0, 0.0] if Aim is None else Aim
        self.HasAim = False if HasAim is None else HasAim
        self.Fire = [False, False] if Fire is None else Fire
        self.Reload = False if Reload is None else Reload
        self.Pick = 0 if Pick is None else Pick
        self.Take = 0 if Take is None else Take
        self.Drop = 0 if Drop is None else Drop
        self.Label = "" if Label is None else Label


def parse_Hello(d):
    obj = Hello.__new__(Hello)
    obj.Type = d.get("type", "")
    obj.Protocol = d.get("protocol", "")
    obj.Slot = d.get("slot", 0)
    obj.Seed = d.get("seed", 0)
    obj.Map = parse_HelloMap(d.get("map", {}))
    obj.Config = parse_Config(d.get("config", {}))
    return obj


def parse_HelloMap(d):
    obj = HelloMap.__new__(HelloMap)
    obj.Dir = d.get("dir", "")
    obj.Files = d.get("files", [])
    return obj


def parse_ZonePhase(d):
    obj = ZonePhase.__new__(ZonePhase)
    obj.HoldS = d.get("hold_s", 0.0)
    obj.ShrinkS = d.get("shrink_s", 0.0)
    obj.Radius = d.get("radius", 0.0)
    obj.Dps = d.get("dps", 0.0)
    return obj


def parse_Effect(d):
    obj = Effect.__new__(Effect)
    obj.Path = d.get("path", "")
    obj.Mul = d.get("mul", None)
    obj.Add = d.get("add", None)
    return obj


def parse_UpgradeDef(d):
    obj = UpgradeDef.__new__(UpgradeDef)
    obj.ID = d.get("id", "")
    obj.Name = d.get("name", "")
    obj.Desc = d.get("desc", "")
    obj.Requires = d.get("requires", "")
    obj.Max = d.get("max", 0)
    obj.Effects = [parse_Effect(item) for item in (d.get("effects") or ())]
    return obj


def parse_Config(d):
    obj = Config.__new__(Config)
    obj.Match = d.get("match", {})
    obj.Bot = d.get("bot", {})
    obj.Mech = d.get("mech", {})
    obj.Vision = parse_ConfigVision(d.get("vision", {}))
    obj.Sound = parse_ConfigSound(d.get("sound", {}))
    obj.Weapons = d.get("weapons", {})
    obj.Projectile = d.get("projectile", {})
    obj.Cubes = parse_ConfigCubes(d.get("cubes", {}))
    obj.Crates = d.get("crates", {})
    obj.Loot = parse_ConfigLoot(d.get("loot", {}))
    obj.Npc = d.get("npc", {})
    obj.Drops = parse_ConfigDrops(d.get("drops")) if d.get("drops") is not None else None
    obj.Zone = parse_ConfigZone(d.get("zone", {}))
    obj.Replay = d.get("replay", {})
    obj.Debug = d.get("debug", {})
    obj.Upgrades = [parse_UpgradeDef(item) for item in (d.get("upgrades") or ())]
    return obj


def parse_ConfigVision(d):
    obj = ConfigVision.__new__(ConfigVision)
    obj.Range = d.get("range", 0.0)
    obj.FovDeg = d.get("fov_deg", 0.0)
    obj.NearRange = d.get("near_range", 0.0)
    obj.CanopyBlocks = d.get("canopy_blocks", False)
    obj.ShowEnemyHP = d.get("show_enemy_hp", False)
    obj.MemoryS = d.get("memory_s", 0.0)
    return obj


def parse_ConfigSound(d):
    obj = ConfigSound.__new__(ConfigSound)
    obj.BearingNoiseDeg = d.get("bearing_noise_deg", 0.0)
    obj.Near = d.get("near", 0.0)
    obj.Mid = d.get("mid", 0.0)
    obj.StepSpeed = d.get("step_speed", 0.0)
    obj.StepEvery = d.get("step_every", 0.0)
    obj.Range = d.get("range", {})
    return obj


def parse_ConfigCubes(d):
    obj = ConfigCubes.__new__(ConfigCubes)
    obj.PickupRadius = d.get("pickup_radius", 0.0)
    obj.HPPerCube = d.get("hp_per_cube", 0.0)
    obj.DamagePerCube = d.get("damage_per_cube", 0.0)
    obj.StatCap = d.get("stat_cap", 0.0)
    obj.DeathDropExtra = d.get("death_drop_extra", 0.0)
    obj.SizePerCube = d.get("size_per_cube", 0.0)
    obj.UpgradeThresholds = d.get("upgrade_thresholds", [])
    return obj


def parse_ConfigLoot(d):
    obj = ConfigLoot.__new__(ConfigLoot)
    obj.PickupRadius = d.get("pickup_radius", 0.0)
    obj.EquipS = d.get("equip_s", 0.0)
    obj.FloorCount = d.get("floor_count", 0.0)
    obj.FloorRoofFraction = d.get("floor_roof_fraction", 0.0)
    obj.CrateWeaponChance = d.get("crate_weapon_chance", 0.0)
    obj.DeathDrop = d.get("death_drop", 0.0)
    obj.Weights = d.get("weights", {})
    return obj


def parse_ConfigDrops(d):
    obj = ConfigDrops.__new__(ConfigDrops)
    obj.Times = d.get("times", [])
    obj.FallS = d.get("fall_s", 0.0)
    obj.Radius = d.get("radius", 0.0)
    obj.CaptureS = d.get("capture_s", 0.0)
    obj.Cubes = d.get("cubes", 0.0)
    obj.Repair = d.get("repair", 0.0)
    obj.Spread = d.get("spread", 0.0)
    return obj


def parse_ConfigZone(d):
    obj = ConfigZone.__new__(ConfigZone)
    obj.StartCenter = d.get("start_center", [])
    obj.StartRadius = d.get("start_radius", 0.0)
    obj.Phases = [parse_ZonePhase(item) for item in (d.get("phases") or ())]
    return obj


def parse_WeaponObs(d):
    obj = WeaponObs.__new__(WeaponObs)
    obj.Kind = d.get("kind", "")
    obj.Cooldown = d.get("cooldown", 0.0)
    obj.Ammo = d.get("ammo", 0.0)
    obj.Reload = d.get("reload", 0.0)
    obj.Charge = d.get("charge", 0.0)
    obj.Stats = d.get("stats")
    return obj


def parse_SelfObs(d):
    obj = SelfObs.__new__(SelfObs)
    obj.ID = d.get("id", 0)
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    obj.Vel = d.get("vel", [0.0, 0.0, 0.0])
    obj.Aim = d.get("aim", [0.0, 0.0])
    obj.HP = d.get("hp", 0.0)
    obj.MaxHP = d.get("max_hp", 0.0)
    obj.Energy = d.get("energy", 0.0)
    obj.MaxEnergy = d.get("max_energy", 0.0)
    obj.Grounded = d.get("grounded", False)
    obj.Cubes = d.get("cubes", 0)
    obj.Upgrades = d.get("upgrades", [])
    obj.InZone = d.get("in_zone", False)
    obj.Weapons = [(parse_WeaponObs(item) if item is not None else None) for item in (d.get("weapons") or ())]
    obj.Stats = d.get("stats", {})
    return obj


def parse_ActorObs(d):
    obj = ActorObs.__new__(ActorObs)
    obj.ID = d.get("id", 0)
    obj.Kind = d.get("kind", "")
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    obj.Vel = d.get("vel", [0.0, 0.0, 0.0])
    obj.Aim = d.get("aim", [0.0, 0.0])
    obj.HP = d.get("hp", 0.0)
    obj.MaxHP = d.get("max_hp", 0.0)
    obj.Cubes = d.get("cubes", 0)
    obj.Weapons = d.get("weapons", [])
    obj.Charging = d.get("charging", False)
    return obj


def parse_ProjectileObs(d):
    obj = ProjectileObs.__new__(ProjectileObs)
    obj.ID = d.get("id", 0)
    obj.Kind = d.get("kind", "")
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    obj.Vel = d.get("vel", [0.0, 0.0, 0.0])
    return obj


def parse_ItemObs(d):
    obj = ItemObs.__new__(ItemObs)
    obj.ID = d.get("id", 0)
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    obj.HP = d.get("hp", 0.0)
    return obj


def parse_PickupObs(d):
    obj = PickupObs.__new__(PickupObs)
    obj.ID = d.get("id", 0)
    obj.Kind = d.get("kind", "")
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    return obj


def parse_SoundObs(d):
    obj = SoundObs.__new__(SoundObs)
    obj.Kind = d.get("kind", "")
    obj.Bearing = d.get("bearing", 0.0)
    obj.Dist = d.get("dist", "")
    obj.Age = d.get("age", 0.0)
    return obj


def parse_BeamObs(d):
    obj = BeamObs.__new__(BeamObs)
    obj.By = d.get("by", 0)
    obj.Kind = d.get("kind", "")
    obj.Path = d.get("path", [])
    obj.Age = d.get("age", 0.0)
    return obj


def parse_Event(d):
    obj = Event.__new__(Event)
    obj.Type = d.get("type", "")
    obj.Amount = d.get("amount", 0.0)
    obj.Weapon = d.get("weapon", "")
    obj.Bearing = d.get("bearing", None)
    obj.By = d.get("by", None)
    obj.Rear = d.get("rear", False)
    obj.Target = d.get("target", 0)
    obj.Effect = d.get("effect", "")
    obj.ID = parse_IDValue(d.get("id", {}))
    obj.Cubes = d.get("cubes", 0)
    obj.Kind = d.get("kind", "")
    obj.Slot = d.get("slot", 0)
    obj.Reason = d.get("reason", "")
    return obj


def parse_IDValue(d):
    return IDValue(Str=d) if isinstance(d, str) else IDValue(Num=int(d or 0))


def parse_DropObs(d):
    obj = DropObs.__new__(DropObs)
    obj.ID = d.get("id", 0)
    obj.Pos = d.get("pos", [0.0, 0.0, 0.0])
    obj.Radius = d.get("radius", 0.0)
    obj.LandsIn = d.get("lands_in", 0.0)
    obj.CaptureS = d.get("capture_s", 0.0)
    obj.Progress = d.get("progress", 0.0)
    obj.Holder = d.get("holder", None)
    return obj


def parse_ZoneObs(d):
    obj = ZoneObs.__new__(ZoneObs)
    obj.Center = d.get("center", [0.0, 0.0])
    obj.Radius = d.get("radius", 0.0)
    obj.NextCenter = d.get("next_center", [0.0, 0.0])
    obj.NextRadius = d.get("next_radius", 0.0)
    obj.ShrinkStart = d.get("shrink_start", 0.0)
    obj.ShrinkEnd = d.get("shrink_end", 0.0)
    obj.Dps = d.get("dps", 0.0)
    return obj


def parse_OfferChoice(d):
    obj = OfferChoice.__new__(OfferChoice)
    obj.ID = d.get("id", "")
    obj.Name = d.get("name", "")
    obj.Desc = d.get("desc", "")
    return obj


def parse_Offer(d):
    obj = Offer.__new__(Offer)
    obj.ID = d.get("id", 0)
    obj.Expires = d.get("expires", 0.0)
    obj.Choices = [parse_OfferChoice(item) for item in (d.get("choices") or ())]
    return obj


def parse_Obs(d):
    obj = Obs.__new__(Obs)
    obj.Type = d.get("type", "")
    obj.Tick = d.get("tick", 0)
    obj.T = d.get("t", 0.0)
    obj.Alive = d.get("alive", 0)
    obj.Self = parse_SelfObs(d.get("self", {}))
    obj.Mechs = [parse_ActorObs(item) for item in (d.get("mechs") or ())]
    obj.Projectiles = [parse_ProjectileObs(item) for item in (d.get("projectiles") or ())]
    obj.Crates = [parse_ItemObs(item) for item in (d.get("crates") or ())]
    obj.Cubes = [parse_ItemObs(item) for item in (d.get("cubes") or ())]
    obj.Pickups = [parse_PickupObs(item) for item in (d.get("pickups") or ())]
    obj.Sounds = [parse_SoundObs(item) for item in (d.get("sounds") or ())]
    obj.Beams = [parse_BeamObs(item) for item in (d.get("beams") or ())]
    obj.Events = [parse_Event(item) for item in (d.get("events") or ())]
    obj.Drops = [parse_DropObs(item) for item in (d.get("drops") or ())]
    obj.Zone = parse_ZoneObs(d.get("zone", {}))
    obj.Offer = parse_Offer(d.get("offer")) if d.get("offer") is not None else None
    return obj


def parse_Action(d):
    obj = Action.__new__(Action)
    obj.Tick = d.get("tick", 0)
    obj.Move = d.get("move", [0.0, 0.0])
    obj.Boost = d.get("boost", False)
    obj.Jump = d.get("jump", False)
    obj.Aim = d.get("aim", [0.0, 0.0])
    obj.HasAim = d.get("hasaim", False)
    obj.Fire = d.get("fire", [False, False])
    obj.Reload = d.get("reload", False)
    obj.Pick = d.get("pick", 0)
    obj.Take = d.get("take", 0)
    obj.Drop = d.get("drop", 0)
    obj.Label = d.get("label", "")
    return obj


hello = parse_Hello
observation = obs = parse_Obs


def NewAction(tick):
    return Action(Tick=tick, Pick=-1, Take=-1, Drop=-1)


def _rounded(value, precision):
    return round(value, precision) if abs(value) <= 1e15 else 0


def action(a):
    result = {
        "tick": a.Tick,
        "move": [_rounded(v, 4) for v in a.Move],
        "boost": bool(a.Boost),
        "jump": bool(a.Jump),
        "fire": list(a.Fire),
    }
    if a.HasAim:
        result["aim"] = [_rounded(v, 5) for v in a.Aim]
    if a.Reload:
        result["reload"] = True
    for name, value in (("pick", a.Pick), ("take", a.Take), ("drop", a.Drop)):
        if value >= 0:
            result[name] = value
    if a.Label:
        result["debug"] = {"label": a.Label.encode()[:70].decode(errors="replace")}
    return result
