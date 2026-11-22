# Python decision engine, translated from the pinned Go revision.
from copy import copy
import math
from pathlib import Path
import gzip
import struct
import sys
import os
import world
import protocol as proto
from gorandom import GoRand
from semantics import (
    go_Contains,
    go_Fprintf,
    go_Slice,
    go_Sprintf,
    go_div,
    go_f32,
    go_getenv,
    go_inf,
    go_intcast,
    go_intdiv,
    go_len,
    go_remainder,
)

_MISSING = object()

fireLatency = 0.075
hmEnclosed = 1
hmGround = 0
hmNone = 255
hmRoof = 2
roofApproach = 1
roofClimb = 2
roofNone = 0
roofOn = 3
seenCell = 32
trkHist = 40


class Params:
    __slots__ = [
        "Name",
        "EngageRatio",
        "DisengageRat",
        "RetreatHP",
        "ReturnHP",
        "LeadDamp",
        "GunMaxRange",
        "StrafeMin",
        "StrafeMax",
        "LootRadius",
        "WantCubes",
        "DropGreed",
        "Hunt",
        "PracticeAware",
        "FFAEngage",
        "FFADisengage",
        "FFALootRadius",
        "FFAWantCubes",
        "FFAReturnFire",
        "Salt",
        "ForceFFA",
        "SlotRule",
        "CloseDisengage",
        "DuelDisengage",
        "UseRoofs",
        "RoofInSquad",
        "RoofMaxClimb",
        "RoofMinHeight",
        "RoofMinZone",
        "ArmRadius",
        "OpenSecs",
        "CreditOpenS",
        "DropRadius",
        "LeaveTTD",
        "PatientSecs",
        "PatientCubes",
        "PatientRange",
        "UseHideMap",
        "HideSeenW",
        "HideHitW",
        "HideDistW",
        "HideClimbW",
        "HideStick",
        "StealthFightRange",
        "QuietHoldS",
        "LaserValue",
        "LightningValue",
        "ArmSwapMin",
        "HitModel",
        "PlanV2",
        "KiteNeedsLaser",
        "ExchangeW",
        "Brawl",
        "BrawlEngage",
        "BrawlDisengage",
        "BrawlHunt",
        "BrawlLootRadius",
        "BrawlWantCubes",
        "AvoidAdv",
        "AvoidRange",
        "AvoidCover",
        "CoverFirst",
        "CoverMinRange",
        "EdgeHold",
        "RunOnRange",
        "RunOnGain",
        "CoverMargin",
        "ShySecs",
        "ShyRange",
        "ShyLaser",
        "ShyMem",
        "ShyBoost",
        "ShyLootRadius",
        "ShyExposure",
        "RetreatRunMax",
        "RetreatRunLaser",
        "LootHiddenBias",
        "CoverEdgeAdv",
        "HuntLaserEdge",
        "Peek",
        "PeekCover",
        "PeekReach",
        "PeekMinRange",
        "OverlandEarly",
        "RoofCoverHold",
        "RoofStandCheck",
        "DropStick",
        "ClimbClearRange",
        "RoofCenterW",
        "RoofLeaveQuiet",
        "ZoneSlack",
        "BrawlRoofs",
        "BrawlRoofCubes",
        "BrawlRoofAfter",
        "Jink",
        "LeadPersist",
        "LeadCum",
        "LeadCumMin",
        "LaserPreempt",
        "AvoidCoverLaser",
        "HoldHideMap",
        "LaserAimRange",
        "PathFix",
        "CreditFix",
        "LootBoost",
        "NoMortar",
        "ProvokeRule",
        "PlinkMaxDPS",
        "HuntRange",
        "HuntRangeLaser",
        "KiteMin",
        "KiteMax",
        "RoofFirstSecs",
        "RoofFirstDist",
        "AllNoMortar",
        "CookoffAware",
        "AntiLightningW",
        "AntiLightningPad",
        "LaserDodgeV2",
        "LaserBeamW",
        "SquadLaserCover",
        "SmartFireV2",
        "LaserEarlyRel",
        "RearBonus",
        "CookoffBonus",
        "CautiousT",
        "BeamFFA",
        "FinalHold",
        "SquadPeek",
        "NanoBoost",
        "RegenHoldHP",
        "ThreatFocus",
        "LightKiteBoost",
    ]

    def __init__(
        self,
        Name="",
        EngageRatio=0.0,
        DisengageRat=0.0,
        RetreatHP=0.0,
        ReturnHP=0.0,
        LeadDamp=0.0,
        GunMaxRange=0.0,
        StrafeMin=0.0,
        StrafeMax=0.0,
        LootRadius=0.0,
        WantCubes=0,
        DropGreed=0.0,
        Hunt=False,
        PracticeAware=False,
        FFAEngage=0.0,
        FFADisengage=0.0,
        FFALootRadius=0.0,
        FFAWantCubes=0,
        FFAReturnFire=0.0,
        Salt=0,
        ForceFFA=False,
        SlotRule=False,
        CloseDisengage=0.0,
        DuelDisengage=0.0,
        UseRoofs=False,
        RoofInSquad=False,
        RoofMaxClimb=0.0,
        RoofMinHeight=0.0,
        RoofMinZone=0.0,
        ArmRadius=0.0,
        OpenSecs=0.0,
        CreditOpenS=0.0,
        DropRadius=0.0,
        LeaveTTD=0.0,
        PatientSecs=0.0,
        PatientCubes=0,
        PatientRange=0.0,
        UseHideMap=False,
        HideSeenW=0.0,
        HideHitW=0.0,
        HideDistW=0.0,
        HideClimbW=0.0,
        HideStick=0.0,
        StealthFightRange=0.0,
        QuietHoldS=0.0,
        LaserValue=0.0,
        LightningValue=0.0,
        ArmSwapMin=0.0,
        HitModel=0,
        PlanV2=False,
        KiteNeedsLaser=False,
        ExchangeW=0.0,
        Brawl=False,
        BrawlEngage=0.0,
        BrawlDisengage=0.0,
        BrawlHunt=False,
        BrawlLootRadius=0.0,
        BrawlWantCubes=0,
        AvoidAdv=0.0,
        AvoidRange=0.0,
        AvoidCover=0.0,
        CoverFirst=False,
        CoverMinRange=0.0,
        EdgeHold=0.0,
        RunOnRange=0.0,
        RunOnGain=0.0,
        CoverMargin=0.0,
        ShySecs=0.0,
        ShyRange=0.0,
        ShyLaser=0.0,
        ShyMem=0.0,
        ShyBoost=0.0,
        ShyLootRadius=0.0,
        ShyExposure=0.0,
        RetreatRunMax=0.0,
        RetreatRunLaser=0.0,
        LootHiddenBias=0.0,
        CoverEdgeAdv=0.0,
        HuntLaserEdge=False,
        Peek=False,
        PeekCover=0.0,
        PeekReach=0.0,
        PeekMinRange=0.0,
        OverlandEarly=0.0,
        RoofCoverHold=0.0,
        RoofStandCheck=False,
        DropStick=False,
        ClimbClearRange=0.0,
        RoofCenterW=0.0,
        RoofLeaveQuiet=0.0,
        ZoneSlack=0.0,
        BrawlRoofs=False,
        BrawlRoofCubes=0,
        BrawlRoofAfter=0.0,
        Jink=0.0,
        LeadPersist=False,
        LeadCum=False,
        LeadCumMin=0.0,
        LaserPreempt=False,
        AvoidCoverLaser=0.0,
        HoldHideMap=False,
        LaserAimRange=0.0,
        PathFix=False,
        CreditFix=False,
        LootBoost=0.0,
        NoMortar=False,
        ProvokeRule=False,
        PlinkMaxDPS=0.0,
        HuntRange=0.0,
        HuntRangeLaser=0.0,
        KiteMin=0.0,
        KiteMax=0.0,
        RoofFirstSecs=0.0,
        RoofFirstDist=0.0,
        AllNoMortar=False,
        CookoffAware=False,
        AntiLightningW=0.0,
        AntiLightningPad=0.0,
        LaserDodgeV2=False,
        LaserBeamW=0.0,
        SquadLaserCover=False,
        SmartFireV2=False,
        LaserEarlyRel=False,
        RearBonus=0.0,
        CookoffBonus=0.0,
        CautiousT=0.0,
        BeamFFA=False,
        FinalHold=False,
        SquadPeek=False,
        NanoBoost=0.0,
        RegenHoldHP=0.0,
        ThreatFocus=False,
        LightKiteBoost=False,
    ):
        self.Name = Name
        self.EngageRatio = EngageRatio
        self.DisengageRat = DisengageRat
        self.RetreatHP = RetreatHP
        self.ReturnHP = ReturnHP
        self.LeadDamp = LeadDamp
        self.GunMaxRange = GunMaxRange
        self.StrafeMin = StrafeMin
        self.StrafeMax = StrafeMax
        self.LootRadius = LootRadius
        self.WantCubes = WantCubes
        self.DropGreed = DropGreed
        self.Hunt = Hunt
        self.PracticeAware = PracticeAware
        self.FFAEngage = FFAEngage
        self.FFADisengage = FFADisengage
        self.FFALootRadius = FFALootRadius
        self.FFAWantCubes = FFAWantCubes
        self.FFAReturnFire = FFAReturnFire
        self.Salt = Salt
        self.ForceFFA = ForceFFA
        self.SlotRule = SlotRule
        self.CloseDisengage = CloseDisengage
        self.DuelDisengage = DuelDisengage
        self.UseRoofs = UseRoofs
        self.RoofInSquad = RoofInSquad
        self.RoofMaxClimb = RoofMaxClimb
        self.RoofMinHeight = RoofMinHeight
        self.RoofMinZone = RoofMinZone
        self.ArmRadius = ArmRadius
        self.OpenSecs = OpenSecs
        self.CreditOpenS = CreditOpenS
        self.DropRadius = DropRadius
        self.LeaveTTD = LeaveTTD
        self.PatientSecs = PatientSecs
        self.PatientCubes = PatientCubes
        self.PatientRange = PatientRange
        self.UseHideMap = UseHideMap
        self.HideSeenW = HideSeenW
        self.HideHitW = HideHitW
        self.HideDistW = HideDistW
        self.HideClimbW = HideClimbW
        self.HideStick = HideStick
        self.StealthFightRange = StealthFightRange
        self.QuietHoldS = QuietHoldS
        self.LaserValue = LaserValue
        self.LightningValue = LightningValue
        self.ArmSwapMin = ArmSwapMin
        self.HitModel = HitModel
        self.PlanV2 = PlanV2
        self.KiteNeedsLaser = KiteNeedsLaser
        self.ExchangeW = ExchangeW
        self.Brawl = Brawl
        self.BrawlEngage = BrawlEngage
        self.BrawlDisengage = BrawlDisengage
        self.BrawlHunt = BrawlHunt
        self.BrawlLootRadius = BrawlLootRadius
        self.BrawlWantCubes = BrawlWantCubes
        self.AvoidAdv = AvoidAdv
        self.AvoidRange = AvoidRange
        self.AvoidCover = AvoidCover
        self.CoverFirst = CoverFirst
        self.CoverMinRange = CoverMinRange
        self.EdgeHold = EdgeHold
        self.RunOnRange = RunOnRange
        self.RunOnGain = RunOnGain
        self.CoverMargin = CoverMargin
        self.ShySecs = ShySecs
        self.ShyRange = ShyRange
        self.ShyLaser = ShyLaser
        self.ShyMem = ShyMem
        self.ShyBoost = ShyBoost
        self.ShyLootRadius = ShyLootRadius
        self.ShyExposure = ShyExposure
        self.RetreatRunMax = RetreatRunMax
        self.RetreatRunLaser = RetreatRunLaser
        self.LootHiddenBias = LootHiddenBias
        self.CoverEdgeAdv = CoverEdgeAdv
        self.HuntLaserEdge = HuntLaserEdge
        self.Peek = Peek
        self.PeekCover = PeekCover
        self.PeekReach = PeekReach
        self.PeekMinRange = PeekMinRange
        self.OverlandEarly = OverlandEarly
        self.RoofCoverHold = RoofCoverHold
        self.RoofStandCheck = RoofStandCheck
        self.DropStick = DropStick
        self.ClimbClearRange = ClimbClearRange
        self.RoofCenterW = RoofCenterW
        self.RoofLeaveQuiet = RoofLeaveQuiet
        self.ZoneSlack = ZoneSlack
        self.BrawlRoofs = BrawlRoofs
        self.BrawlRoofCubes = BrawlRoofCubes
        self.BrawlRoofAfter = BrawlRoofAfter
        self.Jink = Jink
        self.LeadPersist = LeadPersist
        self.LeadCum = LeadCum
        self.LeadCumMin = LeadCumMin
        self.LaserPreempt = LaserPreempt
        self.AvoidCoverLaser = AvoidCoverLaser
        self.HoldHideMap = HoldHideMap
        self.LaserAimRange = LaserAimRange
        self.PathFix = PathFix
        self.CreditFix = CreditFix
        self.LootBoost = LootBoost
        self.NoMortar = NoMortar
        self.ProvokeRule = ProvokeRule
        self.PlinkMaxDPS = PlinkMaxDPS
        self.HuntRange = HuntRange
        self.HuntRangeLaser = HuntRangeLaser
        self.KiteMin = KiteMin
        self.KiteMax = KiteMax
        self.RoofFirstSecs = RoofFirstSecs
        self.RoofFirstDist = RoofFirstDist
        self.AllNoMortar = AllNoMortar
        self.CookoffAware = CookoffAware
        self.AntiLightningW = AntiLightningW
        self.AntiLightningPad = AntiLightningPad
        self.LaserDodgeV2 = LaserDodgeV2
        self.LaserBeamW = LaserBeamW
        self.SquadLaserCover = SquadLaserCover
        self.SmartFireV2 = SmartFireV2
        self.LaserEarlyRel = LaserEarlyRel
        self.RearBonus = RearBonus
        self.CookoffBonus = CookoffBonus
        self.CautiousT = CautiousT
        self.BeamFFA = BeamFFA
        self.FinalHold = FinalHold
        self.SquadPeek = SquadPeek
        self.NanoBoost = NanoBoost
        self.RegenHoldHP = RegenHoldHP
        self.ThreatFocus = ThreatFocus
        self.LightKiteBoost = LightKiteBoost


class Track:
    __slots__ = [
        "ID",
        "NPC",
        "Pos",
        "Vel",
        "Aim",
        "HP",
        "MaxHP",
        "Cubes",
        "Laser",
        "Mortar",
        "Light",
        "Gun",
        "Charging",
        "LastSeen",
        "Listed",
        "LOS",
        "LOST",
        "HurtMeT",
        "HurtMe",
        "IHurtT",
        "IHurt",
        "AimAtMeT",
        "SeenT0",
        "PhantomT",
        "WasListed",
        "ViewT",
        "EngT",
        "hist",
        "hn",
        "hi",
        "leadN",
        "missNone",
        "missLead",
    ]

    def __init__(
        self,
        ID=0,
        NPC=False,
        Pos=_MISSING,
        Vel=_MISSING,
        Aim=_MISSING,
        HP=0.0,
        MaxHP=0.0,
        Cubes=0,
        Laser=False,
        Mortar=False,
        Light=False,
        Gun=False,
        Charging=False,
        LastSeen=0.0,
        Listed=False,
        LOS=False,
        LOST=0.0,
        HurtMeT=0.0,
        HurtMe=0.0,
        IHurtT=0.0,
        IHurt=0.0,
        AimAtMeT=0.0,
        SeenT0=0.0,
        PhantomT=0.0,
        WasListed=False,
        ViewT=0.0,
        EngT=0.0,
        hist=_MISSING,
        hn=0,
        hi=0,
        leadN=0.0,
        missNone=0.0,
        missLead=0.0,
    ):
        self.ID = ID
        self.NPC = NPC
        self.Pos = [0.0] * 3 if Pos is _MISSING else Pos
        self.Vel = [0.0] * 3 if Vel is _MISSING else Vel
        self.Aim = [0.0] * 2 if Aim is _MISSING else Aim
        self.HP = HP
        self.MaxHP = MaxHP
        self.Cubes = Cubes
        self.Laser = Laser
        self.Mortar = Mortar
        self.Light = Light
        self.Gun = Gun
        self.Charging = Charging
        self.LastSeen = LastSeen
        self.Listed = Listed
        self.LOS = LOS
        self.LOST = LOST
        self.HurtMeT = HurtMeT
        self.HurtMe = HurtMe
        self.IHurtT = IHurtT
        self.IHurt = IHurt
        self.AimAtMeT = AimAtMeT
        self.SeenT0 = SeenT0
        self.PhantomT = PhantomT
        self.WasListed = WasListed
        self.ViewT = ViewT
        self.EngT = EngT
        self.hist = [trkSample() for _ in range(40)] if hist is _MISSING else hist
        self.hn = hn
        self.hi = hi
        self.leadN = leadN
        self.missNone = missNone
        self.missLead = missLead

    def __copy__(self):
        other = object.__new__(type(self))
        other.ID = self.ID
        other.NPC = self.NPC
        other.Pos = self.Pos.copy()
        other.Vel = self.Vel.copy()
        other.Aim = self.Aim.copy()
        other.HP = self.HP
        other.MaxHP = self.MaxHP
        other.Cubes = self.Cubes
        other.Laser = self.Laser
        other.Mortar = self.Mortar
        other.Light = self.Light
        other.Gun = self.Gun
        other.Charging = self.Charging
        other.LastSeen = self.LastSeen
        other.Listed = self.Listed
        other.LOS = self.LOS
        other.LOST = self.LOST
        other.HurtMeT = self.HurtMeT
        other.HurtMe = self.HurtMe
        other.IHurtT = self.IHurtT
        other.IHurt = self.IHurt
        other.AimAtMeT = self.AimAtMeT
        other.SeenT0 = self.SeenT0
        other.PhantomT = self.PhantomT
        other.WasListed = self.WasListed
        other.ViewT = self.ViewT
        other.EngT = self.EngT
        other.hist = [copy(item) for item in self.hist]
        other.hn = self.hn
        other.hi = self.hi
        other.leadN = self.leadN
        other.missNone = self.missNone
        other.missLead = self.missLead
        return other

    def scale(t, sizePerCube):
        return 1 + (sizePerCube * float(t.Cubes))


class trkSample:
    __slots__ = ["t", "x", "y", "vx", "vy", "facing"]

    def __init__(self, t=0.0, x=0.0, y=0.0, vx=0.0, vy=0.0, facing=False):
        self.t = t
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.facing = facing


class modeRec:
    __slots__ = ["t", "mode"]

    def __init__(self, t=0.0, mode=""):
        self.t = t
        self.mode = mode


class hitRec:
    __slots__ = ["t", "amt"]

    def __init__(self, t=0.0, amt=0.0):
        self.t = t
        self.amt = amt


class dmgRec:
    __slots__ = ["t", "by", "weapon", "amt", "d", "seen"]

    def __init__(self, t=0.0, by=0, weapon="", amt=0.0, d=0.0, seen=False):
        self.t = t
        self.by = by
        self.weapon = weapon
        self.amt = amt
        self.d = d
        self.seen = seen


class Item:
    __slots__ = ["ID", "Pos", "HP", "Kind", "LastSeen", "Ground", "Cell"]

    def __init__(self, ID=0, Pos=_MISSING, HP=0.0, Kind="", LastSeen=0.0, Ground=False, Cell=0):
        self.ID = ID
        self.Pos = [0.0] * 3 if Pos is _MISSING else Pos
        self.HP = HP
        self.Kind = Kind
        self.LastSeen = LastSeen
        self.Ground = Ground
        self.Cell = Cell

    def __copy__(self):
        other = object.__new__(type(self))
        other.ID = self.ID
        other.Pos = self.Pos.copy()
        other.HP = self.HP
        other.Kind = self.Kind
        other.LastSeen = self.LastSeen
        other.Ground = self.Ground
        other.Cell = self.Cell
        return other


class slot:
    __slots__ = ["ok", "kind", "cooldown", "ammo", "reload", "charge", "stats"]

    def __init__(self, ok=False, kind="", cooldown=0.0, ammo=0.0, reload=0.0, charge=0.0, stats=_MISSING):
        self.ok = ok
        self.kind = kind
        self.cooldown = cooldown
        self.ammo = ammo
        self.reload = reload
        self.charge = charge
        self.stats = {} if stats is _MISSING else stats


class Bot:
    __slots__ = [
        "P",
        "H",
        "C",
        "W",
        "Nav",
        "rng",
        "dt",
        "decide",
        "sizePerCube",
        "o",
        "t",
        "pos",
        "vel",
        "aim",
        "hp",
        "maxHP",
        "energy",
        "scale",
        "radius",
        "height",
        "eyeH",
        "muzzleH",
        "walk",
        "boostV",
        "turn",
        "pitchR",
        "armor",
        "slots",
        "tracks",
        "crates",
        "cubes",
        "pickups",
        "lastDamageT",
        "lastWeaponDT",
        "lastDealtT",
        "recentDmg",
        "lastDmgBear",
        "lastDmgBy",
        "lastSoundT",
        "lastSoundB",
        "path",
        "pathBad",
        "pathSet",
        "pathGoal",
        "pathT",
        "pathIdx",
        "strafeSign",
        "strafeT",
        "stuckT",
        "stuckPos",
        "stuckFor",
        "unstickT",
        "unstickDir",
        "lastMove",
        "mode",
        "targetID",
        "retreating",
        "coverCell",
        "coverT",
        "deepCell",
        "deepT",
        "deepTryT",
        "standT",
        "creditAbsorbT",
        "nearCoverT",
        "nearCoverOK",
        "lootID",
        "lootT",
        "holdCell",
        "holdT",
        "lastAimCmd",
        "scanPhase",
        "laserHold",
        "takeT",
        "ffaSeenT",
        "ffaBeams",
        "kills",
        "killsSeen",
        "deadSeen",
        "unexplained",
        "ffa",
        "st",
        "evadeCell",
        "evadeT",
        "hideT",
        "lastLabel",
        "modeLabel",
        "lastTraceT",
        "lastNpcDT",
        "seenT",
        "seenNX",
        "seenNY",
        "roamCell",
        "roamT",
        "dmgLog",
        "modeLog",
        "hitLog",
        "lowT",
        "retreatT",
        "corneredT",
        "zgKey",
        "zgT",
        "zgComp",
        "zgGoal",
        "zgWalk",
        "myComp",
        "mainCompID",
        "surf",
        "surfGoal",
        "surfT",
        "surfIdx",
        "surfBan",
        "surfWatchT",
        "surfWatchPos",
        "surfPushing",
        "banUntil",
        "roof",
        "roofCoverC",
        "roofCoverT",
        "unquietT",
        "peek",
        "roofCoverHoldT",
        "holdClimb",
        "holdRoofMove",
        "jinkSign",
        "jinkT",
        "edgeOnT",
        "slipCell",
        "slipT",
        "slipOnT",
        "hm",
        "hideCell",
        "hideOut",
        "hideOutOK",
        "hideOutT",
        "roofFirstOK",
        "roofFirstChecked",
        "roofSecs",
        "dmgOnRoof",
        "dmgOffRoof",
        "dmgClimb",
        "climbs",
        "prevRoofState",
        "creditT",
        "creditID",
        "scratch",
    ]

    def __init__(
        self,
        P=_MISSING,
        H=None,
        C=None,
        W=None,
        Nav=None,
        rng=None,
        dt=0.0,
        decide=0.0,
        sizePerCube=0.0,
        o=None,
        t=0.0,
        pos=_MISSING,
        vel=_MISSING,
        aim=_MISSING,
        hp=0.0,
        maxHP=0.0,
        energy=0.0,
        scale=0.0,
        radius=0.0,
        height=0.0,
        eyeH=0.0,
        muzzleH=0.0,
        walk=0.0,
        boostV=0.0,
        turn=0.0,
        pitchR=0.0,
        armor=0.0,
        slots=_MISSING,
        tracks=_MISSING,
        crates=_MISSING,
        cubes=_MISSING,
        pickups=_MISSING,
        lastDamageT=0.0,
        lastWeaponDT=0.0,
        lastDealtT=0.0,
        recentDmg=0.0,
        lastDmgBear=0.0,
        lastDmgBy=0,
        lastSoundT=0.0,
        lastSoundB=0.0,
        path=_MISSING,
        pathBad=False,
        pathSet=False,
        pathGoal=_MISSING,
        pathT=0.0,
        pathIdx=0,
        strafeSign=0.0,
        strafeT=0.0,
        stuckT=0.0,
        stuckPos=_MISSING,
        stuckFor=0.0,
        unstickT=0.0,
        unstickDir=_MISSING,
        lastMove=_MISSING,
        mode="",
        targetID=0,
        retreating=False,
        coverCell=0,
        coverT=0.0,
        deepCell=0,
        deepT=0.0,
        deepTryT=0.0,
        standT=0.0,
        creditAbsorbT=0.0,
        nearCoverT=0.0,
        nearCoverOK=False,
        lootID=0,
        lootT=0.0,
        holdCell=0,
        holdT=0.0,
        lastAimCmd=_MISSING,
        scanPhase=0.0,
        laserHold=False,
        takeT=0.0,
        ffaSeenT=0.0,
        ffaBeams=0,
        kills=0,
        killsSeen=0,
        deadSeen=0,
        unexplained=0,
        ffa=False,
        st=_MISSING,
        evadeCell=0,
        evadeT=0.0,
        hideT=0.0,
        lastLabel="",
        modeLabel="",
        lastTraceT=0.0,
        lastNpcDT=0.0,
        seenT=_MISSING,
        seenNX=0,
        seenNY=0,
        roamCell=0,
        roamT=0.0,
        dmgLog=_MISSING,
        modeLog=_MISSING,
        hitLog=_MISSING,
        lowT=0.0,
        retreatT=0.0,
        corneredT=0.0,
        zgKey=_MISSING,
        zgT=0.0,
        zgComp=0,
        zgGoal=_MISSING,
        zgWalk=False,
        myComp=0,
        mainCompID=0,
        surf=_MISSING,
        surfGoal=_MISSING,
        surfT=0.0,
        surfIdx=0,
        surfBan=_MISSING,
        surfWatchT=0.0,
        surfWatchPos=_MISSING,
        surfPushing=False,
        banUntil=_MISSING,
        roof=_MISSING,
        roofCoverC=0,
        roofCoverT=0.0,
        unquietT=0.0,
        peek=_MISSING,
        roofCoverHoldT=0.0,
        holdClimb=False,
        holdRoofMove=False,
        jinkSign=0.0,
        jinkT=0.0,
        edgeOnT=0.0,
        slipCell=0,
        slipT=0.0,
        slipOnT=0.0,
        hm=None,
        hideCell=0,
        hideOut=_MISSING,
        hideOutOK=False,
        hideOutT=0.0,
        roofFirstOK=False,
        roofFirstChecked=False,
        roofSecs=0.0,
        dmgOnRoof=0.0,
        dmgOffRoof=0.0,
        dmgClimb=0.0,
        climbs=0,
        prevRoofState=0,
        creditT=0.0,
        creditID=0,
        scratch=_MISSING,
    ):
        self.P = Params() if P is _MISSING else P
        self.H = H
        self.C = C
        self.W = W
        self.Nav = Nav
        self.rng = rng
        self.dt = dt
        self.decide = decide
        self.sizePerCube = sizePerCube
        self.o = o
        self.t = t
        self.pos = [0.0] * 3 if pos is _MISSING else pos
        self.vel = [0.0] * 3 if vel is _MISSING else vel
        self.aim = [0.0] * 2 if aim is _MISSING else aim
        self.hp = hp
        self.maxHP = maxHP
        self.energy = energy
        self.scale = scale
        self.radius = radius
        self.height = height
        self.eyeH = eyeH
        self.muzzleH = muzzleH
        self.walk = walk
        self.boostV = boostV
        self.turn = turn
        self.pitchR = pitchR
        self.armor = armor
        self.slots = [slot() for _ in range(2)] if slots is _MISSING else slots
        self.tracks = {} if tracks is _MISSING else tracks
        self.crates = {} if crates is _MISSING else crates
        self.cubes = {} if cubes is _MISSING else cubes
        self.pickups = {} if pickups is _MISSING else pickups
        self.lastDamageT = lastDamageT
        self.lastWeaponDT = lastWeaponDT
        self.lastDealtT = lastDealtT
        self.recentDmg = recentDmg
        self.lastDmgBear = lastDmgBear
        self.lastDmgBy = lastDmgBy
        self.lastSoundT = lastSoundT
        self.lastSoundB = lastSoundB
        self.path = [] if path is _MISSING else path
        self.pathBad = pathBad
        self.pathSet = pathSet
        self.pathGoal = [0.0] * 2 if pathGoal is _MISSING else pathGoal
        self.pathT = pathT
        self.pathIdx = pathIdx
        self.strafeSign = strafeSign
        self.strafeT = strafeT
        self.stuckT = stuckT
        self.stuckPos = [0.0] * 3 if stuckPos is _MISSING else stuckPos
        self.stuckFor = stuckFor
        self.unstickT = unstickT
        self.unstickDir = [0.0] * 2 if unstickDir is _MISSING else unstickDir
        self.lastMove = [0.0] * 2 if lastMove is _MISSING else lastMove
        self.mode = mode
        self.targetID = targetID
        self.retreating = retreating
        self.coverCell = coverCell
        self.coverT = coverT
        self.deepCell = deepCell
        self.deepT = deepT
        self.deepTryT = deepTryT
        self.standT = standT
        self.creditAbsorbT = creditAbsorbT
        self.nearCoverT = nearCoverT
        self.nearCoverOK = nearCoverOK
        self.lootID = lootID
        self.lootT = lootT
        self.holdCell = holdCell
        self.holdT = holdT
        self.lastAimCmd = [0.0] * 2 if lastAimCmd is _MISSING else lastAimCmd
        self.scanPhase = scanPhase
        self.laserHold = laserHold
        self.takeT = takeT
        self.ffaSeenT = ffaSeenT
        self.ffaBeams = ffaBeams
        self.kills = kills
        self.killsSeen = killsSeen
        self.deadSeen = deadSeen
        self.unexplained = unexplained
        self.ffa = ffa
        self.st = stance() if st is _MISSING else st
        self.evadeCell = evadeCell
        self.evadeT = evadeT
        self.hideT = hideT
        self.lastLabel = lastLabel
        self.modeLabel = modeLabel
        self.lastTraceT = lastTraceT
        self.lastNpcDT = lastNpcDT
        self.seenT = None if seenT is _MISSING else seenT
        self.seenNX = seenNX
        self.seenNY = seenNY
        self.roamCell = roamCell
        self.roamT = roamT
        self.dmgLog = [] if dmgLog is _MISSING else dmgLog
        self.modeLog = [] if modeLog is _MISSING else modeLog
        self.hitLog = [] if hitLog is _MISSING else hitLog
        self.lowT = lowT
        self.retreatT = retreatT
        self.corneredT = corneredT
        self.zgKey = [0.0] * 3 if zgKey is _MISSING else zgKey
        self.zgT = zgT
        self.zgComp = zgComp
        self.zgGoal = [0.0] * 2 if zgGoal is _MISSING else zgGoal
        self.zgWalk = zgWalk
        self.myComp = myComp
        self.mainCompID = mainCompID
        self.surf = [] if surf is _MISSING else surf
        self.surfGoal = [0.0] * 2 if surfGoal is _MISSING else surfGoal
        self.surfT = surfT
        self.surfIdx = surfIdx
        self.surfBan = {} if surfBan is _MISSING else surfBan
        self.surfWatchT = surfWatchT
        self.surfWatchPos = [0.0] * 3 if surfWatchPos is _MISSING else surfWatchPos
        self.surfPushing = surfPushing
        self.banUntil = {} if banUntil is _MISSING else banUntil
        self.roof = roofPlan() if roof is _MISSING else roof
        self.roofCoverC = roofCoverC
        self.roofCoverT = roofCoverT
        self.unquietT = unquietT
        self.peek = peekPlan() if peek is _MISSING else peek
        self.roofCoverHoldT = roofCoverHoldT
        self.holdClimb = holdClimb
        self.holdRoofMove = holdRoofMove
        self.jinkSign = jinkSign
        self.jinkT = jinkT
        self.edgeOnT = edgeOnT
        self.slipCell = slipCell
        self.slipT = slipT
        self.slipOnT = slipOnT
        self.hm = hm
        self.hideCell = hideCell
        self.hideOut = hideout() if hideOut is _MISSING else hideOut
        self.hideOutOK = hideOutOK
        self.hideOutT = hideOutT
        self.roofFirstOK = roofFirstOK
        self.roofFirstChecked = roofFirstChecked
        self.roofSecs = roofSecs
        self.dmgOnRoof = dmgOnRoof
        self.dmgOffRoof = dmgOffRoof
        self.dmgClimb = dmgClimb
        self.climbs = climbs
        self.prevRoofState = prevRoofState
        self.creditT = creditT
        self.creditID = creditID
        self.scratch = [] if scratch is _MISSING else scratch

    def __copy__(self):
        other = object.__new__(type(self))
        other.P = copy(self.P)
        other.H = self.H
        other.C = self.C
        other.W = self.W
        other.Nav = self.Nav
        other.rng = self.rng
        other.dt = self.dt
        other.decide = self.decide
        other.sizePerCube = self.sizePerCube
        other.o = self.o
        other.t = self.t
        other.pos = self.pos.copy()
        other.vel = self.vel.copy()
        other.aim = self.aim.copy()
        other.hp = self.hp
        other.maxHP = self.maxHP
        other.energy = self.energy
        other.scale = self.scale
        other.radius = self.radius
        other.height = self.height
        other.eyeH = self.eyeH
        other.muzzleH = self.muzzleH
        other.walk = self.walk
        other.boostV = self.boostV
        other.turn = self.turn
        other.pitchR = self.pitchR
        other.armor = self.armor
        other.slots = [copy(item) for item in self.slots]
        other.tracks = self.tracks
        other.crates = self.crates
        other.cubes = self.cubes
        other.pickups = self.pickups
        other.lastDamageT = self.lastDamageT
        other.lastWeaponDT = self.lastWeaponDT
        other.lastDealtT = self.lastDealtT
        other.recentDmg = self.recentDmg
        other.lastDmgBear = self.lastDmgBear
        other.lastDmgBy = self.lastDmgBy
        other.lastSoundT = self.lastSoundT
        other.lastSoundB = self.lastSoundB
        other.path = self.path
        other.pathBad = self.pathBad
        other.pathSet = self.pathSet
        other.pathGoal = self.pathGoal.copy()
        other.pathT = self.pathT
        other.pathIdx = self.pathIdx
        other.strafeSign = self.strafeSign
        other.strafeT = self.strafeT
        other.stuckT = self.stuckT
        other.stuckPos = self.stuckPos.copy()
        other.stuckFor = self.stuckFor
        other.unstickT = self.unstickT
        other.unstickDir = self.unstickDir.copy()
        other.lastMove = self.lastMove.copy()
        other.mode = self.mode
        other.targetID = self.targetID
        other.retreating = self.retreating
        other.coverCell = self.coverCell
        other.coverT = self.coverT
        other.deepCell = self.deepCell
        other.deepT = self.deepT
        other.deepTryT = self.deepTryT
        other.standT = self.standT
        other.creditAbsorbT = self.creditAbsorbT
        other.nearCoverT = self.nearCoverT
        other.nearCoverOK = self.nearCoverOK
        other.lootID = self.lootID
        other.lootT = self.lootT
        other.holdCell = self.holdCell
        other.holdT = self.holdT
        other.lastAimCmd = self.lastAimCmd.copy()
        other.scanPhase = self.scanPhase
        other.laserHold = self.laserHold
        other.takeT = self.takeT
        other.ffaSeenT = self.ffaSeenT
        other.ffaBeams = self.ffaBeams
        other.kills = self.kills
        other.killsSeen = self.killsSeen
        other.deadSeen = self.deadSeen
        other.unexplained = self.unexplained
        other.ffa = self.ffa
        other.st = copy(self.st)
        other.evadeCell = self.evadeCell
        other.evadeT = self.evadeT
        other.hideT = self.hideT
        other.lastLabel = self.lastLabel
        other.modeLabel = self.modeLabel
        other.lastTraceT = self.lastTraceT
        other.lastNpcDT = self.lastNpcDT
        other.seenT = self.seenT
        other.seenNX = self.seenNX
        other.seenNY = self.seenNY
        other.roamCell = self.roamCell
        other.roamT = self.roamT
        other.dmgLog = self.dmgLog
        other.modeLog = self.modeLog
        other.hitLog = self.hitLog
        other.lowT = self.lowT
        other.retreatT = self.retreatT
        other.corneredT = self.corneredT
        other.zgKey = self.zgKey.copy()
        other.zgT = self.zgT
        other.zgComp = self.zgComp
        other.zgGoal = self.zgGoal.copy()
        other.zgWalk = self.zgWalk
        other.myComp = self.myComp
        other.mainCompID = self.mainCompID
        other.surf = self.surf
        other.surfGoal = self.surfGoal.copy()
        other.surfT = self.surfT
        other.surfIdx = self.surfIdx
        other.surfBan = self.surfBan
        other.surfWatchT = self.surfWatchT
        other.surfWatchPos = self.surfWatchPos.copy()
        other.surfPushing = self.surfPushing
        other.banUntil = self.banUntil
        other.roof = copy(self.roof)
        other.roofCoverC = self.roofCoverC
        other.roofCoverT = self.roofCoverT
        other.unquietT = self.unquietT
        other.peek = copy(self.peek)
        other.roofCoverHoldT = self.roofCoverHoldT
        other.holdClimb = self.holdClimb
        other.holdRoofMove = self.holdRoofMove
        other.jinkSign = self.jinkSign
        other.jinkT = self.jinkT
        other.edgeOnT = self.edgeOnT
        other.slipCell = self.slipCell
        other.slipT = self.slipT
        other.slipOnT = self.slipOnT
        other.hm = self.hm
        other.hideCell = self.hideCell
        other.hideOut = copy(self.hideOut)
        other.hideOutOK = self.hideOutOK
        other.hideOutT = self.hideOutT
        other.roofFirstOK = self.roofFirstOK
        other.roofFirstChecked = self.roofFirstChecked
        other.roofSecs = self.roofSecs
        other.dmgOnRoof = self.dmgOnRoof
        other.dmgOffRoof = self.dmgOffRoof
        other.dmgClimb = self.dmgClimb
        other.climbs = self.climbs
        other.prevRoofState = self.prevRoofState
        other.creditT = self.creditT
        other.creditID = self.creditID
        other.scratch = self.scratch
        return other

    def trace(b, act):
        if (b.modeLabel == b.lastLabel) and ((b.t - b.lastTraceT) < 5):
            return
        b.lastLabel, b.lastTraceT = b.modeLabel, b.t
        tg = ""
        tr = b.tracks.get(b.targetID, None)
        if tr is not None:
            tg = go_Sprintf(" tgt=%d d=%.0f los=%v hp=%.0f", tr.ID, dist3(b.pos, tr.Pos), tr.LOS, tr.HP)
        w = ""
        i = 0
        while i < 2:
            if b.slots[i].ok:
                w += b.slots[i].kind[:3] + " "
            i += 1
        go_Fprintf(
            sys.stderr,
            "[%d] t=%6.1f alive=%2d hp=%4.0f/%4.0f en=%3.0f cubes=%2d pos=(%.0f,%.0f,%.0f) %-18s w=%s proj=%d mv=(%+.1f,%+.1f)%s%s\n",
            b.H.Slot,
            b.t,
            b.o.Alive,
            b.hp,
            b.maxHP,
            b.energy,
            b.o.Self.Cubes,
            b.pos[0],
            b.pos[1],
            b.pos[2],
            b.modeLabel,
            w,
            go_len(b.o.Projectiles),
            act.Move[0],
            act.Move[1],
            {True: " BOOST", False: ""}.get(act.Boost, ""),
            tg,
        )
        if go_Contains(b.modeLabel, "zone"):
            z = b.o.Zone
            go_Fprintf(
                sys.stderr,
                "      zone cur=(%.0f,%.0f r%.0f) dcur=%.0f next=(%.0f,%.0f r%.0f) dnext=%.0f shrink=%.0f..%.0f inzone=%v goal=(%.0f,%.0f) walk=%v comp=%d ground=%v jump=%v\n",
                z.Center[0],
                z.Center[1],
                z.Radius,
                hyp((b.pos[0] - z.Center[0]), (b.pos[1] - z.Center[1])),
                z.NextCenter[0],
                z.NextCenter[1],
                z.NextRadius,
                hyp((b.pos[0] - z.NextCenter[0]), (b.pos[1] - z.NextCenter[1])),
                z.ShrinkStart,
                z.ShrinkEnd,
                b.o.Self.InZone,
                b.zgGoal[0],
                b.zgGoal[1],
                b.zgWalk,
                b.myComp,
                b.onGroundLevel(),
                act.Jump,
            )

    def Act(b, o):
        # Act is one decision.
        act = proto.NewAction(o.Tick)
        b.observe(o)
        b.think(act)
        if Trace:
            b.trace(act)
        if (Stats and (o.Tick > 0)) and (go_remainder(o.Tick, 600) == 0):
            w = ""
            i = 0
            while i < 2:
                if b.slots[i].ok:
                    w += b.slots[i].kind + "+"
                i += 1
            go_Fprintf(
                sys.stderr,
                "[stat] t=%d stance=%s weapons=%s cubes=%d hp=%.0f alive=%d\n",
                int(b.t),
                b.st.name,
                w,
                o.Self.Cubes,
                b.hp,
                o.Alive,
            )
            go_Fprintf(
                sys.stderr,
                "[roof] t=%d onroof_s=%.0f offroof_s=%.0f dmg_on=%.0f dmg_off=%.0f dmg_climb=%.0f climbs=%d\n",
                int(b.t),
                b.roofSecs,
                (b.t - b.roofSecs),
                b.dmgOnRoof,
                b.dmgOffRoof,
                b.dmgClimb,
                b.climbs,
            )
        if Stats:
            on = (b.onRoof() >= 0) and o.Self.Grounded
            if on:
                b.roofSecs += b.decide
            for i_2 in range(len(o.Events)):
                e = o.Events[i_2]
                if (e.Type == "damaged") and (e.Weapon != "zone"):
                    if on:
                        b.dmgOnRoof += e.Amount
                    elif b.roof.state == roofClimb:
                        b.dmgClimb += e.Amount
                    else:
                        b.dmgOffRoof += e.Amount
            if (b.roof.state == roofClimb) and (b.prevRoofState != roofClimb):
                b.climbs += 1
            b.prevRoofState = b.roof.state
        if ((Stats and (b.hp < 220)) and ((b.t - b.lowT) > 15)) and (go_len(b.dmgLog) > 0):
            b.lowT = b.t
            pass
            by = {}
            first = b.t
            total = 0.0
            for r in b.dmgLog:
                if (b.t - r.t) > 12:
                    continue
                a = by.get(r.by, None)
                if a is None:
                    a = agg_Act()
                    by[r.by] = a
                a.dmg += r.amt
                a.n += 1
                a.w = r.weapon
                if r.d >= 0:
                    a.d = r.d
                if r.seen:
                    a.seen += 1
                if r.t < first:
                    first = r.t
                total += r.amt
            s = ""
            _tmp_6 = by
            for id_ in list(_tmp_6):
                if id_ not in _tmp_6:
                    continue
                a_2 = _tmp_6[id_]
                s += go_Sprintf(" %d:%s:%.0fdmg:%.0fm:seen%d/%d", id_, a_2.w, a_2.dmg, a_2.d, a_2.seen, a_2.n)
            w_2 = ""
            i_3 = 0
            while i_3 < 2:
                if b.slots[i_3].ok:
                    w_2 += b.slots[i_3].kind + "+"
                i_3 += 1
            modes = {}
            nm = 0
            for mr in b.modeLog:
                if mr.t >= (first - 0.5):
                    modes[mr.mode] = modes.get(mr.mode, 0) + 1
                    nm += 1
            top, topN = "", 0
            _tmp_10 = modes
            for m in list(_tmp_10):
                if m not in _tmp_10:
                    continue
                c = _tmp_10[m]
                if c > topN:
                    top, topN = m, c
            dealt = 0.0
            for hr in b.hitLog:
                if hr.t >= (first - 0.5):
                    dealt += hr.amt
            go_Fprintf(
                sys.stderr,
                "[low] t=%.1f stance=%s mode=%s weapons=%s cubes=%d attackers=%d over=%.1fs total=%.0f dealt=%.0f fightfrac=%.2f |%s\n",
                b.t,
                b.st.name,
                top,
                w_2,
                o.Self.Cubes,
                go_len(by),
                (b.t - first),
                total,
                dealt,
                go_div(float((modes.get("fight", 0) + modes.get("fight+cube", 0))), float(max(nm, 1))),
                s,
            )
        if Stats:
            b.modeLog.append(modeRec(b.t, b.mode))
            if go_len(b.modeLog) > 400:
                b.modeLog = b.modeLog[200:]
        if math.isnan(act.Move[0]) or math.isnan(act.Move[1]):
            act.Move = [0, 0]
        if math.isnan(act.Aim[0]) or math.isnan(act.Aim[1]):
            act.HasAim = False
        b.lastMove = (act.Move).copy()
        if act.HasAim:
            b.lastAimCmd = (act.Aim).copy()
        return copy(act)

    def mech(b, key, def_):
        return stat(b.C.Mech, key, def_)

    def observe(b, o):
        # observe folds the observation into memory.
        b.o = o
        b.t = o.T
        s = o.Self
        b.pos, b.vel, b.aim = (s.Pos).copy(), (s.Vel).copy(), (s.Aim).copy()
        b.hp, b.maxHP, b.energy = s.HP, s.MaxHP, s.Energy
        if b.maxHP <= 0:
            b.maxHP = 1
        st = s.Stats
        baseMuzzle = b.mech("muzzle_height", 7)
        b.scale = 1 + (b.sizePerCube * float(s.Cubes))
        b.muzzleH = stat(st, "muzzle_height", (baseMuzzle * b.scale))
        b.eyeH = stat(st, "eye_height", (b.mech("eye_height", 8) * b.scale))
        if b.muzzleH < ((baseMuzzle * b.scale) - 1e-6):
            b.muzzleH = baseMuzzle * b.scale
        e = b.mech("eye_height", 8) * b.scale
        if b.eyeH < (e - 1e-6):
            b.eyeH = e
        b.radius = max(stat(st, "radius", 0), (b.mech("radius", 2.5) * b.scale))
        b.height = max(stat(st, "height", 0), (b.mech("height", 9) * b.scale))
        b.walk = stat(st, "walk_speed", b.mech("walk_speed", 11.7))
        b.boostV = stat(st, "boost_speed", b.mech("boost_speed", 19.5))
        b.turn = stat(st, "turn_rate", b.mech("turn_rate", 4))
        b.pitchR = stat(st, "pitch_rate", b.mech("pitch_rate", 3))
        b.armor = stat(st, "armor", 0)
        i = 0
        while i < 2:
            b.slots[i] = slot()
            if (i < go_len(s.Weapons)) and (s.Weapons[i] is not None):
                w = s.Weapons[i]
                b.slots[i] = slot(
                    ok=True,
                    kind=w.Kind,
                    cooldown=w.Cooldown,
                    ammo=w.Ammo,
                    reload=w.Reload,
                    charge=w.Charge,
                    stats=w.Stats,
                )
                if b.slots[i].stats is None:
                    b.slots[i].stats = b.C.Weapons.get(w.Kind, {})
            i += 1
        b.recentDmg *= math.exp(((-b.decide) / 3.0))
        _tmp_14 = b.tracks
        for _ in list(_tmp_14):
            if _ not in _tmp_14:
                continue
            tr = _tmp_14[_]
            tr.WasListed = tr.Listed
            tr.Listed = False
            tr.LOS = False
            tr.HurtMe *= math.exp(((-b.decide) / 4.0))
            tr.IHurt *= math.exp(((-b.decide) / 4.0))
        c = b.Nav.Nearest(b.pos[0], b.pos[1], 2.9, 9, 4)
        if (c >= 0) and b.onGroundLevel():
            b.myComp = b.Nav.Components()[c]
        eye = [b.pos[0], b.pos[1], (b.pos[2] + b.eyeH)]
        fovHalf = (b.C.Vision.FovDeg * math.pi) / 360
        if fovHalf <= 0:
            fovHalf = math.pi / 3
        visRange = b.C.Vision.Range + stat(s.Stats, "vision_bonus", 0)
        nearRange = b.C.Vision.NearRange + stat(s.Stats, "near_range_bonus", 0)
        for i_2 in range(len(o.Mechs)):
            m = o.Mechs[i_2]
            tr_2 = b.tracks.get(m.ID, None)
            if tr_2 is None:
                tr_2 = Track(
                    ID=m.ID,
                    NPC=(m.Kind == "npc"),
                    HurtMeT=(-100),
                    IHurtT=(-100),
                    AimAtMeT=(-100),
                    LOST=(-100),
                    SeenT0=b.t,
                    PhantomT=(-100),
                    ViewT=(-100),
                    EngT=(-100),
                )
                b.tracks[m.ID] = tr_2
            if (b.t - tr_2.LastSeen) > 6:
                tr_2.SeenT0 = b.t
            tr_2.Pos, tr_2.Vel, tr_2.Aim = (m.Pos).copy(), (m.Vel).copy(), (m.Aim).copy()
            if m.MaxHP > 0:
                tr_2.HP, tr_2.MaxHP = m.HP, m.MaxHP
            elif tr_2.MaxHP == 0:
                tr_2.HP, tr_2.MaxHP = 1400, 1400
            tr_2.Cubes = m.Cubes
            tr_2.Charging = m.Charging
            tr_2.LastSeen = b.t
            tr_2.Listed = True
            if not tr_2.NPC:
                tr_2.Gun, tr_2.Laser, tr_2.Mortar, tr_2.Light = False, False, False, False
                for w_2 in m.Weapons:
                    _tmp_18 = w_2
                    if _tmp_18 == "gun":
                        tr_2.Gun = True
                    elif _tmp_18 == "laser":
                        tr_2.Laser = True
                    elif _tmp_18 == "mortar":
                        tr_2.Mortar = True
                    elif _tmp_18 == "lightning":
                        tr_2.Light = True
            sc = 1.0
            if not tr_2.NPC:
                sc = tr_2.scale(b.sizePerCube)
            ch = 4.5 * sc
            if tr_2.NPC:
                ch = stat(b.C.Npc, "height", 3.5) * 0.5
            tr_2.LOS = b.W.Visible(
                eye[0], eye[1], eye[2], m.Pos[0], m.Pos[1], (m.Pos[2] + ch)
            ) or b.W.Visible(eye[0], eye[1], eye[2], m.Pos[0], m.Pos[1], (m.Pos[2] + (ch * 1.9)))
            if tr_2.LOS:
                tr_2.LOST = b.t
                d3 = dist3(eye, [m.Pos[0], m.Pos[1], (m.Pos[2] + ch)])
                if (d3 < (nearRange - 1)) or (
                    (
                        (d3 < (visRange - 2))
                        and (
                            abs(angDiff(math.atan2((m.Pos[1] - b.pos[1]), (m.Pos[0] - b.pos[0])), b.aim[0]))
                            < (fovHalf - 0.05)
                        )
                    )
                ):
                    tr_2.ViewT = b.t
            if (not tr_2.NPC) and tr_2.LOS:
                bear = math.atan2((b.pos[1] - m.Pos[1]), (b.pos[0] - m.Pos[0]))
                d = dist2(b.pos, m.Pos)
                tol = 0.12 + math.atan2((b.radius * 1.5), max(d, 1))
                off = abs(angDiff(m.Aim[0], bear))
                if off < tol:
                    tr_2.AimAtMeT = b.t
                if b.P.LeadPersist or b.P.LeadCum:
                    b.leadRecord(tr_2, (off < 0.35))
        mem = b.C.Vision.MemoryS
        if mem <= 0:
            mem = 5
        _tmp_20 = b.tracks
        for id_ in list(_tmp_20):
            if id_ not in _tmp_20:
                continue
            tr_3 = _tmp_20[id_]
            if ((b.t - tr_3.LastSeen) > 45) and ((b.t - tr_3.HurtMeT) > 45):
                b.tracks.pop(id_, None)
                continue
            if (tr_3.WasListed and (not tr_3.Listed)) and ((b.t - tr_3.ViewT) < (mem - 1.5)):
                b.tracks.pop(id_, None)
                if b.targetID == id_:
                    b.targetID = -1
        for i_3 in range(len(o.Events)):
            e_2 = o.Events[i_3]
            _tmp_23 = e_2.Type
            if _tmp_23 == "damaged":
                b.lastDamageT = b.t
                if e_2.Weapon == "npc":
                    b.lastNpcDT = b.t
                    if e_2.Bearing is not None:
                        b.lastDmgBear = e_2.Bearing
                    if e_2.By is not None:
                        tr_4 = b.tracks.get(e_2.By, None)
                        if tr_4 is not None:
                            tr_4.HurtMeT = b.t
                elif e_2.Weapon != "zone":
                    b.lastWeaponDT = b.t
                    b.recentDmg += e_2.Amount
                    if e_2.Bearing is not None:
                        b.lastDmgBear = e_2.Bearing
                    if (e_2.By is not None) and (e_2.By != s.ID):
                        b.lastDmgBy = e_2.By
                        tr_5 = b.tracks.get(e_2.By, None)
                        if tr_5 is None:
                            tr_5 = Track(
                                ID=e_2.By,
                                NPC=(e_2.By >= 100),
                                HurtMeT=(-100),
                                IHurtT=(-100),
                                AimAtMeT=(-100),
                                LOST=(-100),
                                SeenT0=b.t,
                                LastSeen=(-100),
                                HP=1400,
                                MaxHP=1400,
                                PhantomT=(-100),
                                ViewT=(-100),
                                EngT=(-100),
                            )
                            b.tracks[e_2.By] = tr_5
                        if ((not tr_5.Listed) and ((b.t - tr_5.LastSeen) > 2)) and (e_2.Bearing is not None):
                            guess = 115.0
                            _tmp_25 = e_2.Weapon
                            if _tmp_25 == "laser":
                                guess = 150
                            elif _tmp_25 == "lightning":
                                guess = 35
                            tr_5.Pos = [
                                (b.pos[0] + (math.cos(e_2.Bearing) * guess)),
                                (b.pos[1] + (math.sin(e_2.Bearing) * guess)),
                                b.pos[2],
                            ]
                            tr_5.Vel = [0.0] * 3
                            tr_5.PhantomT = b.t
                        tr_5.HurtMeT = b.t
                        tr_5.HurtMe += e_2.Amount
                        if Stats:
                            d_2 = -1.0
                            if tr_5.Listed:
                                d_2 = dist2(b.pos, tr_5.Pos)
                            b.dmgLog.append(
                                dmgRec(b.t, e_2.By, e_2.Weapon, e_2.Amount, d_2, (tr_5.Listed and tr_5.LOS))
                            )
                        _tmp_27 = e_2.Weapon
                        if _tmp_27 == "laser":
                            tr_5.Laser = True
                        elif _tmp_27 == "mortar":
                            tr_5.Mortar = True
                        elif _tmp_27 == "lightning":
                            tr_5.Light = True
            elif _tmp_23 == "hit":
                b.lastDealtT = b.t
                if e_2.Target < 100:
                    b.creditT = b.t
                    b.creditID = e_2.Target
                    if Stats:
                        b.hitLog.append(hitRec(b.t, e_2.Amount))
                tr_6 = b.tracks.get(e_2.Target, None)
                if tr_6 is not None:
                    tr_6.IHurtT = b.t
                    tr_6.IHurt += e_2.Amount
            elif _tmp_23 == "kill":
                b.kills += 1
                b.tracks.pop(e_2.Target, None)
                if b.targetID == e_2.Target:
                    b.targetID = -1
            elif _tmp_23 == "took":
                b.pickups.pop(e_2.ID.Num, None)
            elif _tmp_23 == "take_failed":
                if (e_2.Reason == "gone") or (e_2.Reason == "have"):
                    b.pickups.pop(e_2.ID.Num, None)
        b.foldItems(o.Crates, b.crates, "crate")
        b.foldItems(o.Cubes, b.cubes, "cube")
        seen = {}
        for i_4 in range(len(o.Pickups)):
            p = o.Pickups[i_4]
            seen[p.ID] = True
            it = b.pickups.get(p.ID, None)
            if it is None:
                it = Item(ID=p.ID)
                b.pickups[p.ID] = it
            it.Pos, it.Kind, it.LastSeen = (p.Pos).copy(), p.Kind, b.t
            b.groundCheck(it)
        b.expireUnseen(b.pickups, seen, eye)
        for i_5 in range(len(o.Sounds)):
            sd = o.Sounds[i_5]
            _tmp_31 = sd.Kind
            if (
                (_tmp_31 == "gun")
                or (_tmp_31 == "laser")
                or (_tmp_31 == "lightning")
                or (_tmp_31 == "mortar")
                or (_tmp_31 == "laser_charge")
                or (_tmp_31 == "boost")
                or (_tmp_31 == "step")
                or (_tmp_31 == "jet")
                or (_tmp_31 == "reload")
            ):
                if sd.Dist != "far":
                    b.lastSoundT = b.t - sd.Age
                    b.lastSoundB = sd.Bearing
        sawFFABeam = False
        for i_6 in range(len(o.Beams)):
            bm = o.Beams[i_6]
            if bm.By == s.ID:
                continue
            if go_len(bm.Path) >= 2:
                p0 = (bm.Path[0]).copy()
                end = (bm.Path[(go_len(bm.Path) - 1)]).copy()
                segD, _ = segPointDist2D(b.pos[0], b.pos[1], p0[0], p0[1], end[0], end[1])
                if (dist2(end, b.pos) > 25) and (segD > 22):
                    b.ffaSeenT = b.t
                    sawFFABeam = True
        if sawFFABeam:
            b.ffaBeams += 1

    def foldItems(b, list_, m, kind):
        eye = [b.pos[0], b.pos[1], (b.pos[2] + b.eyeH)]
        seen = {}
        for i in range(len(list_)):
            p = list_[i]
            seen[p.ID] = True
            it = m.get(p.ID, None)
            if it is None:
                it = Item(ID=p.ID, Kind=kind)
                m[p.ID] = it
            it.Pos, it.HP, it.LastSeen = (p.Pos).copy(), p.HP, b.t
            b.groundCheck(it)
        b.expireUnseen(m, seen, eye)

    def expireUnseen(b, m, seen, eye):
        # expireUnseen drops remembered items that we should be seeing right now but are not listed.
        near = b.C.Vision.NearRange * 0.85
        _tmp_35 = m
        for id_ in list(_tmp_35):
            if id_ not in _tmp_35:
                continue
            it = _tmp_35[id_]
            if seen.get(id_, False):
                continue
            if (b.t - it.LastSeen) > 240:
                m.pop(id_, None)
                continue
            d = dist3(it.Pos, eye)
            if (d < near) and b.W.Visible(eye[0], eye[1], eye[2], it.Pos[0], it.Pos[1], (it.Pos[2] + 0.8)):
                m.pop(id_, None)

    def groundCheck(b, it):
        # groundCheck marks whether an item can be reached by walking.
        k = b.Nav.Index(it.Pos[0], it.Pos[1])
        it.Cell = k
        it.Ground = False
        if (not b.Nav.Solid[k]) and (abs((float(b.Nav.Z[k]) - it.Pos[2])) < 3.0):
            it.Ground = True
            return
        c = b.Nav.Nearest(it.Pos[0], it.Pos[1], b.radius, b.height, 2)
        if (c >= 0) and (abs((float(b.Nav.Z[c]) - it.Pos[2])) < 3.0):
            it.Cell = c
            it.Ground = True

    def has(b, kind):
        i = 0
        while i < 2:
            if b.slots[i].ok and (b.slots[i].kind == kind):
                return i
            i += 1
        return -1

    def cubeDamageMul(b, cubes):
        capc = b.C.Cubes.StatCap
        c = float(cubes)
        if c > capc:
            c = capc
        return 1 + (b.C.Cubes.DamagePerCube * c)

    def isRear(b, tr):
        if (tr is None) or tr.NPC:
            return False
        halfFront = ((b.mech("front_arc_deg", 180) * 0.5) * math.pi) / 180
        bear = math.atan2((b.pos[1] - tr.Pos[1]), (b.pos[0] - tr.Pos[0]))
        return abs(angDiff(tr.Aim[0], bear)) > halfFront

    def targetOf(b, tr):
        if tr.NPC:
            return aimTarget(
                pos=tr.Pos,
                vel=tr.Vel,
                radius=stat(b.C.Npc, "radius", 1.8),
                centerZ=(stat(b.C.Npc, "height", 3.5) * 0.5),
            )
        sc = tr.scale(b.sizePerCube)
        at = aimTarget(
            pos=tr.Pos,
            vel=tr.Vel,
            radius=(b.mech("radius", 2.5) * sc),
            centerZ=(4.5 * sc),
            mech=True,
            rear=b.isRear(tr),
            hasMortar=tr.Mortar,
        )
        if b.P.LeadPersist or b.P.LeadCum:
            at.gunLead, at.gunLeadSet = b.gunLead(tr), True
        return copy(at)

    def leadDamp(b, tf):
        if tf <= 0.3:
            return 1
        d = 1 - ((((tf - 0.3)) / 0.5) * ((1 - b.P.LeadDamp)))
        if d < b.P.LeadDamp:
            d = b.P.LeadDamp
        return d

    def solveDirect(b, tg, speed, originH):
        # solveDirect computes the aim to hit a target with a straight projectile of the given speed
        # (speed <= 0 means hitscan) leaving from originH above our feet.
        return b.solveDirectLat(tg, speed, originH, fireLatency)

    def solveDirectLat(b, tg, speed, originH, lat):
        ox = b.pos[0] + (b.vel[0] * lat)
        oy = b.pos[1] + (b.vel[1] * lat)
        oz = b.pos[2] + originH
        if not b.o.Self.Grounded:
            oz += b.vel[2] * lat
        tf = 0.0
        px = 0.0
        py = 0.0
        pz = 0.0
        k = 1.0
        if tg.leadSet:
            k = tg.lead
        it = 0
        while it < 4:
            damp = b.leadDamp(tf)
            px = tg.pos[0] + ((tg.vel[0] * ((lat + (tf * damp)))) * k)
            py = tg.pos[1] + ((tg.vel[1] * ((lat + (tf * damp)))) * k)
            vz = clamp(tg.vel[2], (-15), 12)
            pz = (tg.pos[2] + tg.centerZ) + ((vz * ((lat + tf))) * 0.6)
            if speed <= 0:
                break
            d = math.sqrt(
                (((((px - ox)) * ((px - ox))) + (((py - oy)) * ((py - oy)))) + (((pz - oz)) * ((pz - oz))))
            )
            tf = go_div(max(0, (d - 3)), speed)
            it += 1
        hd = hyp((px - ox), (py - oy))
        s = shot(ok=True, tf=tf, point=[px, py, pz])
        s.yaw = math.atan2((py - oy), (px - ox))
        s.pitch = math.atan2((pz - oz), hd)
        s.dist = math.sqrt(((hd * hd) + (((pz - oz)) * ((pz - oz)))))
        if s.dist > 1e-3:
            dx, dy, dz = go_div(((px - ox)), s.dist), go_div(((py - oy)), s.dist), go_div(((pz - oz)), s.dist)
            reach = s.dist - (tg.radius * 0.9)
            if reach < 0.5:
                s.clear = True
            else:
                s.clear = b.W.Raycast(ox, oy, oz, dx, dy, dz, reach) >= (reach - 1e-6)
        else:
            s.clear = True
        return copy(s)

    def solveMortar(b, tg, st):
        # solveMortar computes a ballistic solution (low arc first, high arc when the low one is blocked).
        v = stat(st, "speed", 72)
        g = stat(st, "gravity", 22)
        lat = fireLatency
        ox = b.pos[0] + (b.vel[0] * lat)
        oy = b.pos[1] + (b.vel[1] * lat)
        oz = (b.pos[2] + b.height) + (0.5 * b.scale)
        minP = b.mech("min_pitch", (-0.7))
        maxP = b.mech("max_pitch", 1.3)
        arc = 0
        while arc < 2:
            tf = 0.6
            th = 0.0
            px = 0.0
            py = 0.0
            pz = 0.0
            ok = True
            it = 0
            while it < 5:
                damp = b.leadDamp(tf)
                px = tg.pos[0] + (tg.vel[0] * ((lat + (tf * damp))))
                py = tg.pos[1] + (tg.vel[1] * ((lat + (tf * damp))))
                pz, _ = b.W.Floor(px, py, (tg.pos[2] + 3))
                pz += 0.3
                d = hyp((px - ox), (py - oy))
                if d < 1:
                    ok = False
                    break
                h = pz - oz
                disc = (((v * v) * v) * v) - (g * ((((g * d) * d) + (((2 * h) * v) * v))))
                if disc < 0:
                    ok = False
                    break
                sq = math.sqrt(disc)
                if arc == 0:
                    th = math.atan2(((v * v) - sq), (g * d))
                else:
                    th = math.atan2(((v * v) + sq), (g * d))
                c = math.cos(th)
                if c < 0.05:
                    ok = False
                    break
                tf = go_div(d, ((v * c)))
                it += 1
            if ((not ok) or (th < minP)) or (th > maxP):
                arc += 1
                continue
            if tf > (stat(st, "ttl", 7) - 0.3):
                arc += 1
                continue
            s = shot(ok=True, tf=tf, point=[px, py, pz], pitch=th)
            s.yaw = math.atan2((py - oy), (px - ox))
            s.dist = hyp((px - ox), (py - oy))
            s.clear = True
            cy, sy = math.cos(s.yaw), math.sin(s.yaw)
            vh, vz = (v * math.cos(th)), (v * math.sin(th))
            lx, ly, lz = (
                (ox + ((cy * 3) * math.cos(th))),
                (oy + ((sy * 3) * math.cos(th))),
                (oz + (3 * math.sin(th))),
            )
            n = int((tf / 0.12)) + 2
            i = 1
            while i <= n:
                tt = go_div((tf * float(i)), float(n))
                if i == n:
                    tt = tf - 0.04
                nx, ny, nz = (
                    (ox + ((cy * vh) * tt)),
                    (oy + ((sy * vh) * tt)),
                    ((oz + (vz * tt)) - (((0.5 * g) * tt) * tt)),
                )
                if not b.W.Visible(lx, ly, lz, nx, ny, nz):
                    if hyp((nx - px), (ny - py)) > 3.5:
                        s.clear = False
                    break
                lx, ly, lz = nx, ny, nz
                i += 1
            if s.clear:
                return copy(s)
            arc += 1
        return shot()

    def aimErr(b, s):
        # aimErr returns how far our actual torso is from a solution, after the slew we get before firing.
        ey = abs(angDiff(s.yaw, b.aim[0])) - ((b.turn * b.dt) * 0.9)
        ep = abs((s.pitch - b.aim[1])) - ((b.pitchR * b.dt) * 0.9)
        if ey < 0:
            ey = 0
        if ep < 0:
            ep = 0
        return ey, ep

    def laserDamageAt(b, st, charge):
        full = stat(st, "charge", 0.75)
        mf = stat(st, "min_frac", 0.35)
        f = 1.0
        if full > 0:
            f = clamp(go_div(charge, full), 0, 1)
        return (stat(st, "damage", 315) * ((mf + (((1 - mf)) * f)))) * b.cubeDamageMul(b.o.Self.Cubes)

    def engage(b, act, tg, hasLOS, losRecent, hpLeft, allowFire):
        # engage aims at tg and works the triggers. suppress=false means we may fire.
        # It returns true when something was fired or is charging (for bookkeeping).
        gunI, lasI, ligI, morI = b.has("gun"), b.has("laser"), b.has("lightning"), b.has("mortar")
        gunS = shot()
        lasS = shot()
        morS = shot()
        headTg = copy(tg)
        headOK = False
        if tg.mech:
            headTg.centerZ = tg.centerZ * 1.82
            headTg.radius = tg.radius * 0.8
            headOK = True
        pitchTol = tg.centerZ * 0.8
        if gunI >= 0:
            gunTg, gunHead = copy(tg), copy(headTg)
            if tg.gunLeadSet:
                gunTg.lead, gunTg.leadSet = tg.gunLead, True
                gunHead.lead, gunHead.leadSet = tg.gunLead, True
            gunLat = fireLatency
            if b.P.SmartFireV2:
                if b.slots[gunI].cooldown <= (b.dt + 1e-6):
                    gunLat = b.dt
                else:
                    gunLat = b.decide
            gunS = b.solveDirectLat(gunTg, stat(b.slots[gunI].stats, "speed", 252), b.muzzleH, gunLat)
            if (not gunS.clear) and headOK:
                alt = b.solveDirectLat(gunHead, stat(b.slots[gunI].stats, "speed", 252), b.muzzleH, gunLat)
                if alt.clear:
                    gunS = copy(alt)
                    pitchTol = 0.7
        if (lasI >= 0) or (ligI >= 0):
            lasLat = fireLatency
            if b.P.SmartFireV2:
                lasLat = b.dt
            lasS = b.solveDirectLat(tg, 0, b.muzzleH, lasLat)
            if (not lasS.clear) and headOK:
                alt_2 = b.solveDirectLat(headTg, 0, b.muzzleH, lasLat)
                if alt_2.clear:
                    lasS = copy(alt_2)
                    pitchTol = 0.7
        if morI >= 0:
            morS = b.solveMortar(tg, b.slots[morI].stats)
        d = dist3(
            [b.pos[0], b.pos[1], (b.pos[2] + b.muzzleH)], [tg.pos[0], tg.pos[1], (tg.pos[2] + tg.centerZ)]
        )
        primary = copy(lasS)
        usingMortarAim = False
        gunPrimary = False
        if gunI >= 0:
            primary = copy(gunS)
            gunPrimary = True
        laserReady = False
        if lasI >= 0:
            sl = b.slots[lasI]
            full = stat(sl.stats, "charge", 0.75)
            if (sl.charge > 0) and (
                ((sl.charge >= (full - 0.16)) or (b.laserDamageAt(sl.stats, (sl.charge + 0.1)) >= hpLeft))
            ):
                laserReady = True
                primary = copy(lasS)
                gunPrimary = False
            if gunI < 0:
                primary = copy(lasS)
        if ((((morI >= 0) and morS.ok) and morS.clear) and (b.slots[morI].cooldown <= 0.15)) and (
            not laserReady
        ):
            gunIdle = (
                (((gunI < 0) or (b.slots[gunI].reload > 0)) or (b.slots[gunI].ammo == 0)) or (not gunS.clear)
            ) or (d > b.P.GunMaxRange)
            if allowFire and ((b.mortarWorth(tg, morS, d) or ((gunIdle and (morS.dist > 25))))):
                primary = copy(morS)
                usingMortarAim = True
                gunPrimary = False
        if not primary.ok:
            return
        act.Aim = [primary.yaw, clamp(primary.pitch, b.mech("min_pitch", (-0.7)), b.mech("max_pitch", 1.3))]
        act.HasAim = True
        if (not allowFire) and (not (((lasI >= 0) and (b.slots[lasI].charge > 0)))):
            return
        if (gunI >= 0) and allowFire:
            sl_2 = b.slots[gunI]
            if (sl_2.ammo <= 0) and (sl_2.reload <= 0):
                act.Reload = True
            rng = stat(sl_2.stats, "range", 230)
            maxR = min((rng - 5), b.P.GunMaxRange)
            if not tg.mech:
                maxR = min((rng - 5), 120)
            if (((hasLOS and gunS.clear) and (sl_2.ammo > 0)) and (sl_2.reload <= 0)) and (gunS.dist < maxR):
                ey, ep = b.aimErr(gunS)
                if not gunPrimary:
                    ey = abs(angDiff(gunS.yaw, b.aim[0]))
                    ep = abs((gunS.pitch - b.aim[1]))
                tolY = math.atan2((tg.radius * 0.8), max(gunS.dist, 1))
                tolP = math.atan2(pitchTol, max(gunS.dist, 1))
                if (ey < tolY) and (ep < tolP):
                    act.Fire[gunI] = True
        if lasI >= 0:
            sl_3 = b.slots[lasI]
            rng_2 = stat(sl_3.stats, "range", 280) - 4
            full_2 = stat(sl_3.stats, "charge", 0.75)
            inRange = lasS.dist < rng_2
            if sl_3.charge > 0:
                hold = True
                lasMult = 1.0
                if b.P.SmartFireV2 and tg.rear:
                    lasMult *= b.mech("rear_mult", 1.5)
                if ((b.P.SmartFireV2 or b.P.CookoffAware)) and tg.hasMortar:
                    lasMult *= 1 + stat(b.C.Weapons.get("laser", {}), "cookoff", 0)
                lethal = ((b.laserDamageAt(sl_3.stats, sl_3.charge) * lasMult) >= hpLeft) and (
                    sl_3.charge >= stat(sl_3.stats, "min_charge", 0.15)
                )
                relThr = full_2 - 1e-3
                if b.P.LaserEarlyRel:
                    relThr = (full_2 - b.dt) - 1e-3
                if (((((sl_3.charge >= relThr) or lethal)) and hasLOS) and lasS.clear) and inRange:
                    ey_2, ep_2 = b.aimErr(lasS)
                    tolY_2 = math.atan2((tg.radius * 0.75), max(lasS.dist, 1))
                    tolP_2 = math.atan2((pitchTol * 0.9), max(lasS.dist, 1))
                    if (ey_2 < tolY_2) and (ep_2 < tolP_2):
                        hold = False
                act.Fire[lasI] = hold
                b.laserHold = hold
            elif ((allowFire and (sl_3.cooldown <= 0.12)) and inRange) and ((hasLOS or losRecent)):
                act.Fire[lasI] = True
                b.laserHold = True
        if not allowFire:
            return
        if ligI >= 0:
            sl_4 = b.slots[ligI]
            rng_3 = stat(sl_4.stats, "range", 45)
            cone = (stat(sl_4.stats, "cone_deg", 30) * math.pi) / 180
            cost = stat(sl_4.stats, "energy", 3)
            if (
                (hasLOS and lasS.clear)
                and (
                    d < ((rng_3 - 1.0) - ((0.5 * hyp((tg.vel[0] - b.vel[0]), (tg.vel[1] - b.vel[1]))) * 0.1))
                )
            ) and (b.energy >= cost):
                ey_3 = abs(angDiff(lasS.yaw, b.aim[0])) - ((b.turn * b.dt) * 0.9)
                if ey_3 < (cone * 0.4):
                    act.Fire[ligI] = True
        if ((morI >= 0) and morS.ok) and morS.clear:
            sl_5 = b.slots[morI]
            if (sl_5.cooldown <= 0.05) and usingMortarAim:
                ey_4, ep_3 = b.aimErr(morS)
                if (ey_4 < 0.03) and (ep_3 < 0.02):
                    act.Fire[morI] = True

    def mortarWorth(b, tg, s, d):
        # mortarWorth decides whether a shell at this solution is likely to connect.
        splash = 7.0
        i = b.has("mortar")
        if i >= 0:
            splash = stat(b.slots[i].stats, "splash_radius", 7)
        if s.dist < ((splash + b.radius) + 3):
            return False
        sp = hyp(tg.vel[0], tg.vel[1])
        miss = (sp * s.tf) * 0.5
        if not tg.mech:
            miss = (sp * s.tf) * 0.2
        return miss < (splash * 0.75)

    def idleAim(b, act, heading, haveHeading):
        # idleAim looks along our heading with a slow sweep, or toward the last threat cue.
        yaw = b.aim[0]
        if b.t < 1.75:
            yaw = b.aim[0] + 0.39
        elif ((b.t - b.lastWeaponDT) < 2.5) or ((b.t - b.lastNpcDT) < 2.5):
            yaw = b.lastDmgBear
        elif (b.t - b.lastSoundT) < 1.5:
            yaw = b.lastSoundB
        else:
            b.scanPhase += b.decide
            if haveHeading:
                yaw = heading + (1.9 * math.sin((b.scanPhase * 1.3)))
            else:
                yaw = b.aim[0] + 0.35
        act.Aim = [yaw, 0]
        act.HasAim = True

    def myGunHit(b, d):
        # myGunHit / theirGunHit are the hit-rate models in use (HitModel 0: what we believed before the first
        # real matches, 1: measured).
        if b.realModel():
            return hitTable(d, realMyGun)
        return gunHitProb(d)

    def theirGunHit(b, d):
        if b.realModel():
            return hitTable(d, realTheirGun)
        return theirGunHitProb(d)

    def dpsOf(b, gun, laser, light, mortar, cubes, d, energyOK, gunHit):
        # dps estimates sustained damage per second of a loadout at range d.
        mul = b.cubeDamageMul(cubes)
        w = b.C.Weapons
        total = 0.0
        if gun:
            g = w.get("gun", {})
            cd = stat(g, "cooldown", 0.24)
            mag = stat(g, "mag", 12)
            rl = stat(g, "reload", 2.4)
            if d < stat(g, "range", 230):
                total += go_div((stat(g, "damage", 45) * mag), (((mag * cd) + rl))) * gunHit(d)
        if laser:
            l = w.get("laser", {})
            if d < stat(l, "range", 280):
                lh = 0.85
                if b.realModel():
                    lh = 0.75
                total += (
                    go_div(stat(l, "damage", 315), ((stat(l, "charge", 0.75) + stat(l, "cooldown", 1.65))))
                    * lh
                )
        if light and energyOK:
            l_2 = w.get("lightning", {})
            lr = stat(l_2, "range", 45)
            if b.P.AntiLightningW > 0:
                lr += 6
            if d < lr:
                total += go_div(stat(l_2, "damage", 60), stat(l_2, "cooldown", 0.25))
        if mortar:
            m = w.get("mortar", {})
            if (d > 12) and (d < 200):
                total += go_div(stat(m, "damage", 200), stat(m, "cooldown", 2.6)) * 0.25
        return total * mul

    def myDPS(b, d):
        gun = (b.has("gun") >= 0) and (d < b.P.GunMaxRange)
        return b.dpsOf(
            gun,
            (b.has("laser") >= 0),
            (b.has("lightning") >= 0),
            (b.has("mortar") >= 0),
            b.o.Self.Cubes,
            d,
            (b.energy > 15),
            b.myGunHit,
        )

    def theirDPS(b, tr, d):
        if tr.NPC:
            if d > 95:
                return 0
            return go_div(stat(b.C.Npc, "damage", 25), stat(b.C.Npc, "cooldown", 1)) * 0.5
        gun = tr.Gun or ((((not tr.Laser) and (not tr.Mortar)) and (not tr.Light)))
        laser = tr.Laser
        if laser:
            li = b.has("lightning")
            if ((li >= 0) and (b.energy > 20)) and (d < (stat(b.slots[li].stats, "range", 45) - 3)):
                laser = False
        dps = b.dpsOf(gun, laser, tr.Light, tr.Mortar, tr.Cubes, d, True, b.theirGunHit)
        if (b.P.CookoffAware and laser) and (b.has("mortar") >= 0):
            cook = stat(b.C.Weapons.get("laser", {}), "cookoff", 0)
            if (cook > 0) and (d < stat(b.C.Weapons.get("laser", {}), "range", 280)):
                l = b.C.Weapons.get("laser", {})
                lh = 0.85
                if b.realModel():
                    lh = 0.75
                dps += (
                    (
                        go_div(
                            stat(l, "damage", 315), ((stat(l, "charge", 0.75) + stat(l, "cooldown", 1.65)))
                        )
                        * lh
                    )
                    * cook
                ) * b.cubeDamageMul(tr.Cubes)
        return dps

    def advantage(b, tr, d):
        # advantage is (time they need to kill us) / (time we need to kill them); > 1 favours us.
        mine = b.myDPS(d)
        theirs = b.theirDPS(tr, d) * ((1 - b.armor))
        if mine < 1:
            return 0
        if theirs < 1:
            return 10
        hp = tr.HP
        if hp <= 0:
            hp = tr.MaxHP
        return go_div((go_div(b.hp, theirs)), (go_div(hp, mine)))

    def shyPhase(b, st):
        # shyPhase reports whether the opening rule applies: the first ShySecs of a match in a free-for-all
        # stance (see think for what it does and why).
        return (((b.P.ShySecs > 0) and b.ffa) and st.avoid) and (b.t < b.P.ShySecs)

    def exposedTo(b, secs, maxRange):
        # exposedTo reports whether a mech we saw in the last secs seconds, no farther than maxRange from us,
        # has a clear line from where we last saw it to where we stand. (We only see 120 degrees ahead: a mech
        # that has dropped out of our view has not lost sight of us.)
        _tmp_43 = b.tracks
        for _ in list(_tmp_43):
            if _ not in _tmp_43:
                continue
            tr = _tmp_43[_]
            if tr.NPC or ((b.t - tr.LastSeen) > secs):
                continue
            if hyp((tr.Pos[0] - b.pos[0]), (tr.Pos[1] - b.pos[1])) > maxRange:
                continue
            sc = tr.scale(b.sizePerCube)
            ex, ey, ez = tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))
            if b.W.Visible(ex, ey, ez, b.pos[0], b.pos[1], (b.pos[2] + (b.height * 0.5))) or b.W.Visible(
                ex, ey, ez, b.pos[0], b.pos[1], (b.pos[2] + (b.height * 0.95))
            ):
                return True
        return False

    def mechSeenWithin(b, secs):
        # mechSeenWithin reports whether we have seen another mech in the last secs seconds.
        _tmp_45 = b.tracks
        for _ in list(_tmp_45):
            if _ not in _tmp_45:
                continue
            tr = _tmp_45[_]
            if (not tr.NPC) and ((b.t - tr.LastSeen) <= secs):
                return True
        return False

    def coverClose(b, ths, tgt):
        # coverClose reports whether there is somewhere out of every threat's sight within a few seconds' run:
        # RetreatRunMax metres of path, or RetreatRunLaser when a laser we cannot answer is on us (against that,
        # in the open, nothing else works). The answer is kept for half a second.
        if (b.t - b.nearCoverT) < 0.5:
            return b.nearCoverOK
        reach = b.P.RetreatRunMax
        if (((tgt is not None) and tgt.tr.Laser) and (b.has("laser") < 0)) and (b.P.RetreatRunLaser > reach):
            reach = b.P.RetreatRunLaser
        b.nearCoverT = b.t
        b.nearCoverOK = b.findCover(ths, reach) >= 0
        return b.nearCoverOK

    def deeperCover(b, ths, maxCost, farther):
        # deeperCover returns the nearest cell that is hidden from every recent threat's last known position and
        # from CoverMargin metres to either side of it, with the straight way there out of sight too. With
        # farther set and the nearest threat inside RunOnRange, the cell must also be RunOnGain metres farther
        # from that threat than we are. It returns -1 when where we stand already qualifies, or nothing does.
        pass
        eyes = []
        d0 = 1e9
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((((b.t - tr.LastSeen) > 6) and (not ths[i].phantom))) or (ths[i].d > 260):
                continue
            sc = tr.scale(b.sizePerCube)
            eyes.append(eyeT_deeperCover(tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))))
            d = hyp((tr.Pos[0] - b.pos[0]), (tr.Pos[1] - b.pos[1]))
            if d < d0:
                d0 = d
        if go_len(eyes) == 0:
            return -1
        needFar = (farther and (b.P.RunOnRange > 0)) and (d0 <= b.P.RunOnRange)
        margin = b.P.CoverMargin
        if (margin <= 0) and (not needFar):
            return -1

        def _tmp_48(ex, ey, ez, x, y, gz):
            return b.W.Visible(ex, ey, ez, x, y, (gz + (b.height * 0.5))) or b.W.Visible(
                ex, ey, ez, x, y, (gz + (b.height * 0.95))
            )

        seen = _tmp_48

        def _tmp_49(x_2, y_2, gz_2):
            for e in eyes:
                if seen(e.x, e.y, e.z, x_2, y_2, gz_2):
                    return False
            return True

        hidden = _tmp_49

        def _tmp_51(x_3, y_3, gz_3):
            for e_2 in eyes:
                if seen(e_2.x, e_2.y, e_2.z, x_3, y_3, gz_3):
                    return False
                if margin <= 0:
                    continue
                dx, dy = (x_3 - e_2.x), (y_3 - e_2.y)
                l = hyp(dx, dy)
                if l < 1:
                    return False
                px, py = (go_div((-dy), l) * margin), (go_div(dx, l) * margin)
                if seen((e_2.x + px), (e_2.y + py), e_2.z, x_3, y_3, gz_3) or seen(
                    (e_2.x - px), (e_2.y - py), e_2.z, x_3, y_3, gz_3
                ):
                    return False
            return True

        robust = _tmp_51
        if (not needFar) and robust(b.pos[0], b.pos[1], b.pos[2]):
            return -1
        z = b.o.Zone
        found = -1
        checked = 0

        def _tmp_53(k, cost):
            nonlocal checked
            nonlocal found
            if go_remainder(((go_remainder(k, b.Nav.NX) + go_intdiv(k, b.Nav.NX))), 2) != 0:
                return True
            if float(b.Nav.Clear[k]) < (b.radius + 0.6):
                return True
            x_4, y_4 = b.Nav.Pos(k)
            if hyp((x_4 - z.Center[0]), (y_4 - z.Center[1])) > (z.Radius - 6):
                return True
            if ((z.ShrinkEnd - b.t) < 25) and (
                hyp((x_4 - z.NextCenter[0]), (y_4 - z.NextCenter[1])) > (z.NextRadius - 4)
            ):
                return True
            if needFar:
                de = 1e9
                for e_3 in eyes:
                    d_2 = hyp((x_4 - e_3.x), (y_4 - e_3.y))
                    if d_2 < de:
                        de = d_2
                if de < (d0 + b.P.RunOnGain):
                    return True
            checked += 1
            if checked > 300:
                return False
            if not robust(x_4, y_4, float(b.Nav.Z[k])):
                return True
            for f in [0.25, 0.5, 0.75]:
                mx, my = (b.pos[0] + (((x_4 - b.pos[0])) * f)), (b.pos[1] + (((y_4 - b.pos[1])) * f))
                mk = b.Nav.Index(mx, my)
                if b.Nav.Solid[mk]:
                    continue
                if not hidden(mx, my, float(b.Nav.Z[mk])):
                    return True
            found = k
            return False

        b.Nav.Flood(b.pos[0], b.pos[1], (b.radius + 0.15), b.height, maxCost, None, _tmp_53)
        return found

    def brawlStance(b, name):
        # brawlStance is the free-for-all stance adopted after the first real matches: armed, farming, fighting
        # with an edge and declining coin flips. Also used while we do not know the lobby yet.
        return stance(
            name=name,
            engageRatio=b.P.BrawlEngage,
            disengage=b.P.BrawlDisengage,
            hunt=b.P.BrawlHunt,
            avoid=(b.P.AvoidAdv > 0),
            lootRadius=b.P.BrawlLootRadius,
            wantCubes=b.P.BrawlWantCubes,
        )

    def realModel(b):
        # realModel reports whether the measured (team bot) hit rates apply: in a free-for-all, and until we
        # know better. Against the house squad the older numbers stay (they are what scored in practice).
        if b.P.HitModel < 1:
            return False
        return ((not b.P.PracticeAware) or b.ffa) or b.openPhase()

    def openPhase(b):
        # openPhase reports whether we still do not know what kind of lobby this is: the first OpenSecs, and
        # for CreditOpenS after a death that we put down to our own shooting without having been given the kill
        # (in a free-for-all that is usually somebody else's kill, and one such guess must not send us into the
        # practice stance in the middle of a real fight).
        return (b.t < b.P.OpenSecs) or (
            ((b.P.CreditOpenS > 0) and ((b.t - b.creditAbsorbT) < b.P.CreditOpenS))
        )

    def belief(b):
        # belief updates what we think the lobby is and returns the matching stance.
        total = int(stat(b.C.Match, "mechs", 16))
        dead = total - b.o.Alive
        if dead > b.deadSeen:
            n = dead - b.deadSeen
            b.deadSeen = dead
            if b.kills > b.killsSeen:
                n -= b.kills - b.killsSeen
                b.killsSeen = b.kills
            elif (b.t - b.creditT) < 6:
                mine = True
                if b.P.CreditFix:
                    tr = b.tracks.get(b.creditID, None)
                    if ((tr is not None) and tr.Listed) and (tr.HP > 0):
                        mine = False
                if mine:
                    n -= 1
                    b.creditAbsorbT = b.t
            if n > 0:
                b.unexplained += n
            if ((((b.unexplained >= 1) and (b.t < 35))) or (((b.unexplained >= 2) and (b.t < 110)))) or (
                b.unexplained >= 3
            ):
                b.ffa = True
        alive = b.o.Alive
        if b.P.ForceFFA:
            b.ffa = True
        if b.P.BeamFFA and (b.ffaBeams >= 2):
            b.ffa = True
        if b.P.SlotRule and (b.H.Slot != 0):
            b.ffa = True
        if alive <= 2:
            return stance(
                name="duel", engageRatio=0.0, disengage=0.45, hunt=True, lootRadius=150, wantCubes=40
            )
        elif b.ffa and b.P.PracticeAware:
            if b.P.Brawl:
                return b.brawlStance("ffa")
            return stance(
                name="ffa",
                engageRatio=b.P.FFAEngage,
                disengage=b.P.FFADisengage,
                hunt=False,
                stealth=True,
                lootRadius=b.P.FFALootRadius,
                wantCubes=b.P.FFAWantCubes,
            )
        elif b.openPhase() and b.P.PracticeAware:
            if b.P.Brawl:
                return b.brawlStance("open")
            return stance(
                name="open",
                engageRatio=1.5,
                disengage=0.9,
                hunt=False,
                stealth=True,
                lootRadius=110,
                wantCubes=b.P.WantCubes,
            )
        elif ((b.P.CautiousT > 0) and b.P.PracticeAware) and (
            (
                (b.t >= b.P.CautiousT)
                or ((((b.o.Zone.NextRadius > 0) and (b.o.Zone.NextRadius <= 72)) and (b.t >= 180)))
            )
        ):
            return b.brawlStance("late")
        return stance(
            name="squad",
            engageRatio=b.P.EngageRatio,
            disengage=b.P.DisengageRat,
            hunt=b.P.Hunt,
            lootRadius=b.P.LootRadius,
            wantCubes=b.P.WantCubes,
        )

    def chooseHide(b, zi):
        # chooseHide picks a low-exposure place inside the circle we must end up in. Lower score is better.
        z = b.o.Zone
        exp = b.Nav.Exposure()
        comp = b.Nav.Components()
        myComp = go_intcast(0, 32)
        c = b.Nav.Nearest(b.pos[0], b.pos[1], 2.9, 9, 6)
        if c >= 0:
            myComp = comp[c]
        margin = min(14, (z.NextRadius * 0.25))
        cands = []
        j = 0
        while j < exp.NY:
            i = 0
            while i < exp.NX:
                e = exp.V[((j * exp.NX) + i)]
                if e > 1.5:
                    i += 1
                    continue
                k = exp.Cell(i, j)
                if (myComp != 0) and (comp[k] != myComp):
                    i += 1
                    continue
                x, y = b.Nav.Pos(k)
                dn = hyp((x - z.NextCenter[0]), (y - z.NextCenter[1]))
                if dn > (z.NextRadius - margin):
                    i += 1
                    continue
                if not b.Nav.Walkable(k, (b.radius + 0.4), b.height):
                    i += 1
                    continue
                d = hyp((x - b.pos[0]), (y - b.pos[1]))
                if d > 320:
                    i += 1
                    continue
                s = (float(e) * 100) + (d * b.hideDistW())
                if (z.NextRadius > 60) and (dn < (z.NextRadius * 0.35)):
                    s += 10
                s += float(b.Nav.Clear[k]) * 0.8
                if k == b.holdCell:
                    s -= 9
                cands.append(hideCand(k, s))
                i += 1
            j += 1
        if go_len(cands) == 0:
            return -1

        def _tmp_59(a, c_2):
            return cands[a].score < cands[c_2].score

        go_Slice(cands, _tmp_59)
        if go_len(cands) > 60:
            cands = cands[:60]
        best, bs = (-1), 1e18
        for c_3 in cands:
            x_2, y_2 = b.Nav.Pos(c_3.cell)
            gz = float(b.Nav.Z[c_3.cell])
            s_2 = c_3.score
            _tmp_61 = b.tracks
            for _ in list(_tmp_61):
                if _ not in _tmp_61:
                    continue
                tr = _tmp_61[_]
                if tr.NPC or ((b.t - tr.LastSeen) > 25):
                    continue
                d_2 = hyp((tr.Pos[0] - x_2), (tr.Pos[1] - y_2))
                if d_2 < 90:
                    s_2 += ((90 - d_2)) * 0.35
                if (d_2 < 260) and ((b.t - tr.LastSeen) < 8):
                    sc = tr.scale(b.sizePerCube)
                    if b.W.Visible(
                        tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc)), x_2, y_2, (gz + (b.height * 0.6))
                    ):
                        s_2 += 30
            for i_2 in range(len(b.o.Drops)):
                if hyp((b.o.Drops[i_2].Pos[0] - x_2), (b.o.Drops[i_2].Pos[1] - y_2)) < 70:
                    s_2 += 15
            if s_2 < bs:
                best, bs = c_3.cell, s_2
        return best

    def hideDistW(b):
        if b.st.stealth:
            return 0.16
        return 0.07

    def seenBy(b, ths, maxD):
        # seenBy lists the enemy mechs that currently have a line to us (and are close enough to matter).
        out = []
        for i in range(len(ths)):
            if (ths[i].tr.LOS and ths[i].tr.Listed) and (ths[i].d < maxD):
                out.append(ths[i])
        return out

    def hideDanger(b, seen, hit):
        return 100 * (((b.P.HideSeenW * seen) + (b.P.HideHitW * hit)))

    def chooseHideout(b, zi, allowRoof):
        # chooseHideout picks the least exposed reachable place inside the circle we must end up in, weighing
        # how visible and how hittable it is against the trip there. Lower score is better.
        hm = b.hm
        if hm is None:
            return hideout(), False
        z = b.o.Zone
        nav = b.Nav
        comp = nav.Components()
        roofs, roofOf = nav.Roofs()
        roofDist = nav.RoofDist()
        margin = min(14, (z.NextRadius * 0.25))
        limit = min(b.maxClimb(), b.P.RoofMaxClimb)
        myRoof = -1
        if b.o.Self.Grounded:
            myRoof = b.onRoof()
        walkComp = b.myComp
        if walkComp == 0:
            walkComp = b.mainComp()
        pass
        short = []
        worst = 1e18
        keep = 48
        pass
        roofAcc = []
        if allowRoof:
            roofAcc = [racc_chooseHideout() for _ in range(go_len(roofs))]
        for c in hm.cells:
            k = int(c)
            x, y = nav.Pos(k)
            dn = hyp((x - z.NextCenter[0]), (y - z.NextCenter[1]))
            if dn > (z.NextRadius - margin):
                continue
            d = hyp((x - b.pos[0]), (y - b.pos[1]))
            if d > 380:
                continue
            cl, seen, hit = hm.at(k)
            s = b.hideDanger(seen, hit)
            ho = hideout(cell=k, class_=cl, roof=(-1))
            _tmp_66 = cl
            try:
                if (_tmp_66 == hmGround) or (_tmp_66 == hmEnclosed):
                    if (comp[k] != walkComp) or (not nav.Walkable(k, (b.radius + 0.4), b.height)):
                        continue
                    ho.z = float(nav.Z[k])
                    if myRoof >= 0:
                        s += 6
                elif _tmp_66 == hmRoof:
                    if not allowRoof:
                        continue
                    id_ = int(roofOf[k])
                    if (id_ < 0) or (roofDist[k] < 2):
                        continue
                    until, ok = b.roof.ban.get(id_, 0.0), id_ in b.roof.ban
                    if ok and (b.t < until):
                        continue
                    r = roofs[id_]
                    ho.z, ho.roof = r.Z, id_
                    if id_ == myRoof:
                        raise StopIteration("_tmp_67break")
                    ra = roofAcc[id_]
                    if not ra.done:
                        ra.done = True
                        ra.acc, ra.d, ra.ok = b.roofAccessFor(r, limit)
                    if not ra.ok:
                        continue
                    gx, gy = nav.Pos(ra.acc.Ground)
                    d = ra.d + hyp((x - gx), (y - gy))
                    s += ra.acc.Climb * b.P.HideClimbW
                else:
                    continue
            except StopIteration as _go_flow:
                if _go_flow.args != ("_tmp_67break",):
                    raise
            s += d * b.P.HideDistW
            if k == b.hideCell:
                s -= b.P.HideStick
            ho.score = s
            if go_len(short) < keep:
                short.append(cnd_chooseHideout(ho, d))
                if go_len(short) == keep:
                    worst = -1e18
                    for i in range(len(short)):
                        if short[i].h.score > worst:
                            worst = short[i].h.score
                continue
            if s >= worst:
                continue
            wi = 0
            for i_2 in range(len(short)):
                if short[i_2].h.score > short[wi].h.score:
                    wi = i_2
            short[wi] = cnd_chooseHideout(ho, d)
            worst = -1e18
            for i_3 in range(len(short)):
                if short[i_3].h.score > worst:
                    worst = short[i_3].h.score
        if go_len(short) == 0:
            return hideout(), False
        best = -1
        for i_4 in range(len(short)):
            h = short[i_4].h
            x_2, y_2 = nav.Pos(h.cell)
            s_2 = h.score
            _tmp_72 = b.tracks
            for _ in list(_tmp_72):
                if _ not in _tmp_72:
                    continue
                tr = _tmp_72[_]
                if tr.NPC or ((b.t - tr.LastSeen) > 25):
                    continue
                d_2 = hyp((tr.Pos[0] - x_2), (tr.Pos[1] - y_2))
                if (d_2 < 90) and (abs((tr.Pos[2] - h.z)) < 12):
                    s_2 += ((90 - d_2)) * 0.35
                if (d_2 < 260) and ((b.t - tr.LastSeen) < 8):
                    sc = tr.scale(b.sizePerCube)
                    if b.W.Visible(
                        tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (7 * sc)), x_2, y_2, (h.z + (b.height * 0.5))
                    ):
                        s_2 += 40
                    elif b.W.Visible(
                        tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc)), x_2, y_2, (h.z + b.height)
                    ):
                        s_2 += 12
            for j in range(len(b.o.Drops)):
                if hyp((b.o.Drops[j].Pos[0] - x_2), (b.o.Drops[j].Pos[1] - y_2)) < 70:
                    s_2 += 15
            h.score = s_2
            if (best < 0) or (s_2 < short[best].h.score):
                best = i_4
        return copy(short[best].h), True

    def roofAccessFor(b, r, limit):
        # roofAccessFor returns the nearest usable place to climb a roof from.
        comp = b.Nav.Components()
        acc = world.RoofAccess()
        ad = 1e18
        for a in r.Access:
            if (a.Climb > limit) or (a.Climb < 3):
                continue
            if (b.myComp != 0) and (comp[a.Ground] != b.myComp):
                continue
            if not b.Nav.Walkable(a.Ground, (b.radius + 0.2), b.height):
                continue
            gx, gy = b.Nav.Pos(a.Ground)
            d = hyp((gx - b.pos[0]), (gy - b.pos[1]))
            if d < ad:
                acc, ad = copy(a), d
        return copy(acc), ad, (ad < 1e17)

    def leadRecord(b, tr, facing):
        # leadRecord stores the current observation of a listed mech and scores one virtual shot.
        if tr.hn > 0:
            last = tr.hist[go_remainder((((tr.hi + trkHist) - 1)), trkHist)]
            if ((b.t - last.t) > 0.25) or (b.t <= last.t):
                if b.t <= last.t:
                    return
                tr.hn, tr.hi = 0, 0
        tr.hist[tr.hi] = trkSample(t=b.t, x=tr.Pos[0], y=tr.Pos[1], vx=tr.Vel[0], vy=tr.Vel[1], facing=facing)
        tr.hi = go_remainder(((tr.hi + 1)), trkHist)
        if tr.hn < trkHist:
            tr.hn += 1
        d = hyp((tr.Pos[0] - b.pos[0]), (tr.Pos[1] - b.pos[1]))
        if (d < 55) or (d > 240):
            return
        gunSpd = stat(b.C.Weapons.get("gun", {}), "speed", 252)
        if b.P.SmartFireV2:
            gi = b.has("gun")
            if gi >= 0:
                gunSpd = stat(b.slots[gi].stats, "speed", gunSpd)
        tf = go_div(max(0, (d - 3)), max(gunSpd, 1))
        s = b.leadSample(tr, (b.t - ((fireLatency + tf))))
        if (s is None) or (not s.facing):
            return

        def _tmp_77(px, py):
            ax, ay = norm2((px - b.pos[0]), (py - b.pos[1]))
            return abs((((-((tr.Pos[0] - b.pos[0]))) * ay) + (((tr.Pos[1] - b.pos[1])) * ax)))

        side = _tmp_77
        k = b.leadPersistAt(tr, s.t)
        lead = ((fireLatency + (tf * b.leadDamp(tf)))) * k
        mNone = min(side(s.x, s.y), 6)
        mLead = min(side((s.x + (s.vx * lead)), (s.y + (s.vy * lead))), 6)
        keep = 997 / 1000
        tr.leadN = (tr.leadN * keep) + 1
        tr.missNone = (tr.missNone * keep) + mNone
        tr.missLead = (tr.missLead * keep) + mLead

    def leadSample(b, tr, t):
        # leadSample returns the stored sample closest to time t (nil if none within 0.07 s).
        best = None
        bd = 0.07
        i = 0
        while i < tr.hn:
            s = tr.hist[go_remainder(((((tr.hi + trkHist) - 1) - i)), trkHist)]
            dt = abs((s.t - t))
            if dt < bd:
                best, bd = s, dt
            if s.t < (t - 0.1):
                break
            i += 1
        return best

    def leadPersistAt(b, tr, t):
        # leadPersistAt is how straight the mech had been moving over the 1.2 s before time t: 1 for a steady
        # walk (or when we cannot tell), 0 for jitter on the spot.
        if not b.P.LeadPersist:
            return 1
        first = None
        last = None
        n = 0
        sp = 0.0
        i = 0
        while i < tr.hn:
            s = tr.hist[go_remainder(((((tr.hi + trkHist) - 1) - i)), trkHist)]
            if s.t > (t + 0.01):
                i += 1
                continue
            if s.t < (t - 1.25):
                break
            if last is None:
                last = s
            first = s
            sp += hyp(s.vx, s.vy)
            n += 1
            i += 1
        if ((n < 8) or (last is None)) or ((last.t - first.t) < 0.7):
            return 1
        mean = go_div(hyp((last.x - first.x), (last.y - first.y)), ((last.t - first.t)))
        pers = go_div(mean, max(go_div(sp, float(n)), 0.5))
        return clamp((((pers - 0.2)) / 0.5), 0, 1)

    def gunLead(b, tr):
        # gunLead returns the multiplier to apply to the velocity lead when shooting the gun at this mech.
        if tr.NPC:
            return 1
        if b.P.LeadCum and (tr.leadN >= b.P.LeadCumMin):
            margin = 0.2 * tr.leadN
            if tr.missNone < (tr.missLead - margin):
                return 0
            if tr.missLead < (tr.missNone - margin):
                return 1
        return b.leadPersistAt(tr, b.t)

    def gatherIncoming(b):
        # gatherIncoming lists the visible projectiles that could matter to us in the next couple of seconds.
        out = []
        g = stat(b.C.Weapons.get("mortar", {}), "gravity", 22)
        for i in range(len(b.o.Projectiles)):
            p = b.o.Projectiles[i]
            sp = math.sqrt((((p.Vel[0] * p.Vel[0]) + (p.Vel[1] * p.Vel[1])) + (p.Vel[2] * p.Vel[2])))
            if sp < 1:
                continue
            if p.Kind == "mortar":
                x, y, z = p.Pos[0], p.Pos[1], p.Pos[2]
                vx, vy, vz = p.Vel[0], p.Vel[1], p.Vel[2]
                tt = 0.0
                h = 1 / 20
                hit = False
                while tt < 7:
                    nx, ny, nz = (x + (vx * h)), (y + (vy * h)), ((z + (vz * h)) - (((0.5 * g) * h) * h))
                    if not b.W.Visible(x, y, z, nx, ny, nz):
                        hit = True
                        break
                    x, y, z = nx, ny, nz
                    vz -= g * h
                    tt += h
                if not hit:
                    continue
                splash = stat(b.C.Weapons.get("mortar", {}), "splash_radius", 7) * 1.3
                if dist3([x, y, z], b.pos) > ((splash + b.radius) + 45):
                    continue
                out.append(
                    incoming(
                        mortar=True,
                        pos=p.Pos,
                        vel=p.Vel,
                        maxT=(tt + h),
                        impact=[x, y, z],
                        dmg=stat(b.C.Weapons.get("mortar", {}), "splash", 160),
                        splash=splash,
                    )
                )
                continue
            rx, ry = (b.pos[0] - p.Pos[0]), (b.pos[1] - p.Pos[1])
            along = go_div((((rx * p.Vel[0]) + (ry * p.Vel[1]))), sp)
            if along < (-3):
                continue
            d = hyp(rx, ry)
            if d > 330:
                continue
            lat = go_div(abs(((rx * p.Vel[1]) - (ry * p.Vel[0]))), max(hyp(p.Vel[0], p.Vel[1]), 1))
            if lat > (14 + b.radius):
                continue
            reach = b.W.Raycast(
                p.Pos[0],
                p.Pos[1],
                p.Pos[2],
                go_div(p.Vel[0], sp),
                go_div(p.Vel[1], sp),
                go_div(p.Vel[2], sp),
                (d + 20),
            )
            if reach < ((d - b.radius) - 3):
                continue
            dmg = stat(b.C.Weapons.get("gun", {}), "damage", 45)
            if p.Kind == "npc":
                dmg = stat(b.C.Npc, "damage", 25)
            out.append(incoming(pos=p.Pos, vel=p.Vel, maxT=go_div(reach, sp), dmg=dmg))
        return out

    def steer(b, act, rq):
        # steer evaluates candidate moves by simulating our motion against incoming fire and picks the best.
        grounded = b.o.Self.Grounded
        accel = b.mech("ground_accel", 58.5)
        if not grounded:
            accel = b.mech("air_accel", 12)
        walk = b.walk
        if rq.slow:
            walk *= b.mech("charge_move_mult", 0.5)
        boostV = b.boostV
        if rq.slow:
            boostV *= b.mech("charge_move_mult", 0.5)
        canBoost = (b.energy > 12) and grounded
        horizon = 8
        for i in range(len(rq.threats)):
            k = int(go_div(rq.threats[i].maxT, b.dt)) + 2
            if k > horizon:
                horizon = k
        if horizon > 44:
            horizon = 44
        progTick = 6
        if rq.lookTicks > progTick:
            progTick = rq.lookTicks
            if horizon < progTick:
                horizon = progTick
        cands = b.scratch[:0]
        cands.append(cand(0, 0, False, 0))
        i_2 = 0
        while i_2 < 16:
            cands.append(cand(dirs16[i_2][0], dirs16[i_2][1], False, 0))
            i_2 += 1
        if (rq.wantX != 0) or (rq.wantY != 0):
            cands.append(cand(rq.wantX, rq.wantY, False, 0))
        if canBoost and (((rq.boost or rq.dodgeBoost) or (go_len(rq.threats) > 0))):
            n = go_len(cands)
            i_3 = 1
            while i_3 < n:
                cands.append(cand(cands[i_3].dx, cands[i_3].dy, True, 0))
                i_3 += 1
        zc, zr = (b.o.Zone.Center).copy(), b.o.Zone.Radius
        fence = -1
        roofOf = []
        roofDist = []
        startCell = b.Nav.Index(b.pos[0], b.pos[1])
        startClear = b.Nav.Clear[startCell]
        groundLevel = b.onGroundLevel()
        startRD = go_intcast(0, 16)
        if rq.fenceRoof:
            fence = b.onRoof()
            _, roofOf = b.Nav.Roofs()
            roofDist = b.Nav.RoofDist()
            startRD = roofDist[startCell]
        minClear = go_f32((b.radius * 0.8))
        best = -1
        for ci in range(len(cands)):
            c = cands[ci]
            sp = walk
            if c.boost:
                sp = boostV
            tvx, tvy = (c.dx * sp), (c.dy * sp)
            x, y = b.pos[0], b.pos[1]
            vx, vy = b.vel[0], b.vel[1]
            score = 0.0
            blocked = False
            px = 0.0
            py = 0.0
            k_2 = 1
            while k_2 <= horizon:
                vx, vy = approach2(vx, vy, tvx, tvy, (accel * b.dt))
                nx, ny = (x + (vx * b.dt)), (y + (vy * b.dt))
                cell = b.Nav.Index(nx, ny)
                if cell != startCell:
                    if fence >= 0:
                        if (int(roofOf[cell]) != fence) or (
                            ((roofDist[cell] < 2) and (roofDist[cell] < startRD))
                        ):
                            blocked = True
                            vx, vy = 0, 0
                            nx, ny = x, y
                    elif groundLevel and (
                        (
                            (b.Nav.Solid[cell] or (not b.W.InBounds(nx, ny)))
                            or (((b.Nav.Clear[cell] < minClear) and (b.Nav.Clear[cell] < startClear)))
                        )
                    ):
                        blocked = True
                        vx, vy = 0, 0
                        nx, ny = x, y
                x, y = nx, ny
                if k_2 == progTick:
                    px, py = x, y
                t0 = float((k_2 - 1)) * b.dt
                t1 = float(k_2) * b.dt
                for ti in range(len(rq.threats)):
                    th = rq.threats[ti]
                    if th.mortar:
                        if ((th.maxT > t0) and (th.maxT <= (t1 + 1e-9))) or (
                            ((k_2 == horizon) and (th.maxT > t1))
                        ):
                            d = math.sqrt(
                                (
                                    (
                                        (((x - th.impact[0])) * ((x - th.impact[0])))
                                        + (((y - th.impact[1])) * ((y - th.impact[1])))
                                    )
                                    + (
                                        (((b.pos[2] + (b.height * 0.5)) - th.impact[2]))
                                        * (((b.pos[2] + (b.height * 0.5)) - th.impact[2]))
                                    )
                                )
                            )
                            reach = th.splash + b.radius
                            if d < reach:
                                score -= (th.dmg * ((1 - go_div((0.7 * d), reach)))) + 40
                        continue
                    if t0 >= th.maxT:
                        continue
                    te = min(t1, th.maxT)
                    ax, ay = (th.pos[0] + (th.vel[0] * t0)), (th.pos[1] + (th.vel[1] * t0))
                    bx, by = (th.pos[0] + (th.vel[0] * te)), (th.pos[1] + (th.vel[1] * te))
                    d_2, s = segPointDist2D(x, y, ax, ay, bx, by)
                    if d_2 < ((b.radius + 0.3) + 0.55):
                        tz = th.pos[2] + (th.vel[2] * ((t0 + (((te - t0)) * s))))
                        if (tz > (b.pos[2] - 0.6)) and (tz < ((b.pos[2] + b.height) + 0.6)):
                            score -= th.dmg
                k_2 += 1
            if horizon < progTick:
                px, py = x, y
            score += (((((px - b.pos[0])) * rq.wantX) + (((py - b.pos[1])) * rq.wantY))) * rq.wantW
            if blocked:
                score -= 3
            if (zr > 0) and (not rq.zoneFree):
                dOut = hyp((px - zc[0]), (py - zc[1])) - zr
                dNow = hyp((b.pos[0] - zc[0]), (b.pos[1] - zc[1])) - zr
                if ((dNow < (-0.5)) and (dOut > (-4))) and (dOut > dNow):
                    score -= ((dOut - dNow)) * 8
            if rq.posCost is not None:
                score -= rq.posCost(px, py)
            if c.boost and (not rq.boost):
                score -= 1.5
            if (c.dx == 0) and (c.dy == 0):
                if rq.hold:
                    score += 0.6
            else:
                score += 0.25 * (((c.dx * b.lastMove[0]) + (c.dy * b.lastMove[1])))
            c.score = score
            if (best < 0) or (score > cands[best].score):
                best = ci
        b.scratch = cands
        if best >= 0:
            act.Move = [cands[best].dx, cands[best].dy]
            act.Boost = cands[best].boost

    def onGroundLevel(b):
        # onGroundLevel reports whether our feet are near the walk-grid surface (not on a roof or in the air).
        k = b.Nav.Index(b.pos[0], b.pos[1])
        if b.Nav.Solid[k]:
            return False
        return (b.pos[2] - float(b.Nav.Z[k])) < 3.5

    def navDir(b, gx, gy):
        # navDir returns the direction to walk now to reach (gx,gy) along the ground, and the remaining
        # straight-line distance. ok=false when we have no idea how to get there.
        d = hyp((gx - b.pos[0]), (gy - b.pos[1]))
        if d < 1.0:
            return 0, 0, d, True
        if not b.onGroundLevel():
            dx, dy = norm2((gx - b.pos[0]), (gy - b.pos[1]))
            return dx, dy, d, True
        r, h = (b.radius + 0.15), b.height
        if (d < 14) and b.Nav.WalkLine(b.pos[0], b.pos[1], gx, gy, r, h):
            dx_2, dy_2 = norm2((gx - b.pos[0]), (gy - b.pos[1]))
            return dx_2, dy_2, d, True
        other = (not b.pathSet) or (hyp((gx - b.pathGoal[0]), (gy - b.pathGoal[1])) > 5)
        replan = ((go_len(b.path) == 0) or other) or ((b.t - b.pathT) > 1.6)
        if (not replan) and (b.pathIdx < go_len(b.path)):
            px, py = b.Nav.Pos(int(b.path[b.pathIdx]))
            if hyp((px - b.pos[0]), (py - b.pos[1])) > 12:
                replan = True
        gap = 0.35
        if b.pathBad:
            gap = 1.0
        if other and b.P.PathFix:
            gap = 0.15
        if (replan and ((b.pathSet or (not b.P.PathFix)))) and ((b.t - b.pathT) < gap):
            replan = False
        if (other and (not replan)) and b.P.PathFix:
            dx_3, dy_3 = norm2((gx - b.pos[0]), (gy - b.pos[1]))
            return dx_3, dy_3, d, True
        if replan:
            b.pathSet = True
            b.path = b.Nav.Path(b.pos[0], b.pos[1], gx, gy, r, h, 9000, b.navCost())
            b.pathGoal = [gx, gy]
            b.pathT = b.t
            b.pathIdx = 0
            b.pathBad = go_len(b.path) == 0
            if not b.pathBad:
                lx, ly = b.Nav.Pos(int(b.path[(go_len(b.path) - 1)]))
                b.pathBad = hyp((lx - gx), (ly - gy)) > 7
        if go_len(b.path) == 0:
            dx_4, dy_4 = norm2((gx - b.pos[0]), (gy - b.pos[1]))
            return dx_4, dy_4, d, False
        if b.pathBad:
            lx_2, ly_2 = b.Nav.Pos(int(b.path[(go_len(b.path) - 1)]))
            if hyp((lx_2 - b.pos[0]), (ly_2 - b.pos[1])) < 4:
                dx_5, dy_5 = norm2((gx - b.pos[0]), (gy - b.pos[1]))
                return dx_5, dy_5, d, False
        while b.pathIdx < (go_len(b.path) - 1):
            px_2, py_2 = b.Nav.Pos(int(b.path[b.pathIdx]))
            if hyp((px_2 - b.pos[0]), (py_2 - b.pos[1])) < 3.2:
                b.pathIdx += 1
            else:
                break
        tgt = b.pathIdx
        hi = b.pathIdx + 14
        if hi > (go_len(b.path) - 1):
            hi = go_len(b.path) - 1
        j = hi
        while j > b.pathIdx:
            px_3, py_3 = b.Nav.Pos(int(b.path[j]))
            if b.Nav.WalkLine(b.pos[0], b.pos[1], px_3, py_3, r, h):
                tgt = j
                break
            j -= 2
        if tgt > (b.pathIdx + 1):
            b.pathIdx = tgt - 1
        px_4, py_4 = b.Nav.Pos(int(b.path[tgt]))
        if (tgt == (go_len(b.path) - 1)) and (hyp((gx - px_4), (gy - py_4)) < 4):
            px_4, py_4 = gx, gy
        dx_6, dy_6 = norm2((px_4 - b.pos[0]), (py_4 - b.pos[1]))
        return dx_6, dy_6, d, True

    def unstick(b, act, navigating):
        # unstick notices when we push against something without moving and hops out of it.
        if not navigating:
            b.stuckFor = 0
            b.stuckT = b.t
            b.stuckPos = (b.pos).copy()
            b.unstickT = 0
            return
        moving = hyp(act.Move[0], act.Move[1]) > 0.3
        if (b.t - b.stuckT) >= 0.5:
            moved = dist2(b.pos, b.stuckPos)
            if moving and (moved < 1.2):
                b.stuckFor += b.t - b.stuckT
            else:
                b.stuckFor = 0
            b.stuckT = b.t
            b.stuckPos = (b.pos).copy()
        if (b.stuckFor >= 1.0) and (b.t > b.unstickT):
            a = (b.rng.Float64() * 2) * math.pi
            b.unstickDir = [math.cos(a), math.sin(a)]
            b.unstickT = b.t + 0.7
            b.stuckFor = 0
            b.path = []
        if b.t < b.unstickT:
            act.Move = [((act.Move[0] * 0.4) + b.unstickDir[0]), ((act.Move[1] * 0.4) + b.unstickDir[1])]
            l = hyp(act.Move[0], act.Move[1])
            if l > 1:
                act.Move[0] /= l
                act.Move[1] /= l
            if b.o.Self.Grounded:
                act.Jump = True
            elif b.energy > 30:
                act.Boost = True

    def peekPlanFor(b, tgt, ths, roofID):
        # peekPlanFor works out (or reuses) the two cells against a target. roofID is the roof we are standing
        # on and mean to stay on, or -1.
        if (((b.t - b.peek.t) < 0.4) and (b.peek.tgt == tgt.tr.ID)) and (b.peek.roof == roofID):
            return b.peek.ok
        prevFire = -1
        if (b.peek.ok and (b.peek.tgt == tgt.tr.ID)) and (b.peek.roof == roofID):
            prevFire = b.peek.fire
        b.peek = peekPlan(t=b.t, tgt=tgt.tr.ID, roof=roofID, duck=(-1), fire=(-1))
        tr = tgt.tr
        sc = tr.scale(b.sizePerCube)
        tx, ty, tz = tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (4.5 * sc))
        duck = -1
        if roofID >= 0:
            duck = b.roofCover(roofID, ths)
        else:
            duck = b.findCover(ths, b.P.PeekCover)
        if duck < 0:
            return False
        dx, dy = b.Nav.Pos(duck)
        best, bd = (-1), 1e18

        def _tmp_90(k, z):
            nonlocal bd
            nonlocal best
            x, y = b.Nav.Pos(k)
            d = hyp((x - dx), (y - dy))
            if (d < 1.5) or (d > b.P.PeekReach):
                return
            if k == prevFire:
                d -= 2.5
            if d >= bd:
                return
            if not b.W.Visible(x, y, (z + b.muzzleH), tx, ty, tz):
                return
            best, bd = k, d

        consider = _tmp_90
        if roofID >= 0:
            roofs, roofOf = b.Nav.Roofs()
            dist = b.Nav.RoofDist()
            r = roofs[roofID]
            for c in r.Cells:
                k_2 = int(c)
                if (int(roofOf[k_2]) != roofID) or (dist[k_2] < 2):
                    continue
                consider(k_2, r.Z)
        else:
            ci, cj = go_remainder(duck, b.Nav.NX), go_intdiv(duck, b.Nav.NX)
            rad = int(go_div(b.P.PeekReach, b.Nav.Cell)) + 1
            dj = -rad
            while dj <= rad:
                di = -rad
                while di <= rad:
                    i, j = (ci + di), (cj + dj)
                    if (((i < 0) or (j < 0)) or (i >= b.Nav.NX)) or (j >= b.Nav.NY):
                        di += 1
                        continue
                    k_3 = (j * b.Nav.NX) + i
                    if (not b.Nav.Walkable(k_3, (b.radius + 0.3), b.height)) or (not b.sameComp(k_3)):
                        di += 1
                        continue
                    x_2, y_2 = b.Nav.Pos(k_3)
                    if not b.Nav.WalkLine(dx, dy, x_2, y_2, (b.radius + 0.15), b.height):
                        di += 1
                        continue
                    consider(k_3, float(b.Nav.Z[k_3]))
                    di += 1
                dj += 1
        if best < 0:
            return False
        b.peek.duck, b.peek.fire, b.peek.ok = duck, best, True
        return True

    def peekStep(b, ths, li, hpFrac):
        # peekStep decides, for this decision, whether to stand at the fire cell or the duck cell and whether
        # to start charging now (hidden). Returns the cell to go to and the charge flag.
        cell = 0
        charge = False
        sl = b.slots[li]
        full = stat(sl.stats, "charge", 0.75)
        fx, fy = b.Nav.Pos(b.peek.fire)
        kx, ky = b.Nav.Pos(b.peek.duck)
        travel = go_div(hyp((fx - kx), (fy - ky)), ((b.walk * 0.5))) + 0.15
        atDuck = hyp((b.pos[0] - kx), (b.pos[1] - ky)) < 4
        atFire = hyp((b.pos[0] - fx), (b.pos[1] - fy)) < 4
        threatened = False
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((tr.Laser and tr.Charging) and tr.LOS) and ((b.t - tr.AimAtMeT) < 0.3):
                threatened = True
        cell = b.peek.duck
        if (hpFrac < 0.2) or threatened:
            pass
        elif (sl.charge > 0) and (sl.charge >= (full - travel)):
            cell = b.peek.fire
        elif ((sl.charge <= 0) and (sl.cooldown <= 0.1)) and ((atDuck or atFire)):
            charge = True
        return cell, charge

    def fightPlan(b, tr, d):
        # fightPlan evaluates fighting a mech at several ranges and returns the best advantage ratio together
        # with the range band to hold. The ratio is (time they need to kill us) / (time we need to kill
        # them), after paying for the damage we would take while moving to that range.
        adv = 0.0
        rmin = 0.0
        rmax = 0.0
        hp = tr.HP
        if hp <= 0:
            hp = max(tr.MaxHP, 1)
        pass
        cands = [22, 45, 75, 115, 160, 200]
        bestAdv, bestR = (-1.0), d

        def _tmp_96(r, here):
            nonlocal bestAdv
            nonlocal bestR
            mine = b.myDPS(r)
            theirs = (b.theirDPS(tr, r) * ((1 - b.armor))) * b.dodgeFactor(r, tr)
            if mine < 1:
                return
            move = abs((d - r))
            cost, gain = 0.0, 0.0
            if (not here) and (move > 8):
                mid = ((d + r)) / 2
                cost = (
                    ((b.theirDPS(tr, mid) * ((1 - b.armor))) * b.dodgeFactor(mid, tr)) * ((move / 9.0))
                ) * 0.8
                if b.P.PlanV2 and b.realModel():
                    gain = (b.myDPS(mid) * ((move / 9.0))) * 0.8
                if (r > d) and (not tr.NPC):
                    cost += 60
            left = b.hp - cost
            if left <= 0:
                return
            hpT = hp - gain
            if hpT < 20:
                hpT = 20
            a = 10.0
            if theirs >= 1:
                a = go_div((go_div(left, theirs)), (go_div(hpT, mine)))
            if here:
                a *= 1.05
            if a > bestAdv:
                bestAdv, bestR = a, r

        eval_ = _tmp_96
        eval_(d, True)
        for r_2 in cands:
            eval_(r_2, False)
        if bestAdv < 0:
            return 0, 30, 55
        w = 10 + (bestR * 0.15)
        return bestAdv, max(8, (bestR - w)), (bestR + w)

    def dodgeFactor(b, r, tr):
        # dodgeFactor scales an enemy's expected damage on us at a range: far-off gunfire mostly misses a
        # target that side-steps, lasers and lightning do not care.
        if tr.NPC:
            return 0.6
        return 1

    def markSeen(b):
        # markSeen stamps the coarse cells we can currently see.
        if b.seenT is None:
            b.seenNX = int(math.ceil((((b.W.MaxX - b.W.MinX)) / seenCell))) + 1
            b.seenNY = int(math.ceil((((b.W.MaxY - b.W.MinY)) / seenCell))) + 1
            b.seenT = [0.0] * (b.seenNX * b.seenNY)
            for i in range(len(b.seenT)):
                b.seenT[i] = -1e6
        R = 150
        half = (b.C.Vision.FovDeg * math.pi) / 360
        if half <= 0:
            half = math.pi / 3
        ex, ey, ez = b.pos[0], b.pos[1], (b.pos[2] + b.eyeH)
        i0 = int(((((ex - R) - b.W.MinX)) / seenCell))
        i1 = int(((((ex + R) - b.W.MinX)) / seenCell))
        j0 = int(((((ey - R) - b.W.MinY)) / seenCell))
        j1 = int(((((ey + R) - b.W.MinY)) / seenCell))
        j = j0
        while j <= j1:
            if (j < 0) or (j >= b.seenNY):
                j += 1
                continue
            i_2 = i0
            while i_2 <= i1:
                if (i_2 < 0) or (i_2 >= b.seenNX):
                    i_2 += 1
                    continue
                k = (j * b.seenNX) + i_2
                if float(b.seenT[k]) > (b.t - 2.0):
                    i_2 += 1
                    continue
                cx = b.W.MinX + (((float(i_2) + 0.5)) * seenCell)
                cy = b.W.MinY + (((float(j) + 0.5)) * seenCell)
                d = hyp((cx - ex), (cy - ey))
                if d > R:
                    i_2 += 1
                    continue
                if (d > 40) and (abs(angDiff(math.atan2((cy - ey), (cx - ex)), b.aim[0])) > half):
                    i_2 += 1
                    continue
                gz = b.W.TerrainZ(cx, cy) + 2
                if (d < 20) or b.W.Visible(ex, ey, ez, cx, cy, gz):
                    b.seenT[k] = go_f32(b.t)
                i_2 += 1
            j += 1

    def roamGoal(b):
        # roamGoal picks a ground position worth looking at: not seen for a while, inside the circle, close.
        if b.seenT is None:
            return 0, 0, False
        if ((b.roamCell >= 0) and ((b.t - b.roamT) < 12)) and (float(b.seenT[b.roamCell]) < (b.t - 20)):
            i, j = go_remainder(b.roamCell, b.seenNX), go_intdiv(b.roamCell, b.seenNX)
            x, y = (b.W.MinX + (((float(i) + 0.5)) * seenCell)), (b.W.MinY + (((float(j) + 0.5)) * seenCell))
            c = b.Nav.Nearest(x, y, (b.radius + 0.3), b.height, 8)
            if c >= 0:
                px, py = b.Nav.Pos(c)
                return px, py, True
        z = b.o.Zone
        best, bs = (-1), 1e18
        j_2 = 0
        while j_2 < b.seenNY:
            i_2 = 0
            while i_2 < b.seenNX:
                k = (j_2 * b.seenNX) + i_2
                age = b.t - float(b.seenT[k])
                if age < 45:
                    i_2 += 1
                    continue
                x_2 = b.W.MinX + (((float(i_2) + 0.5)) * seenCell)
                y_2 = b.W.MinY + (((float(j_2) + 0.5)) * seenCell)
                if not b.W.InBounds(x_2, y_2):
                    i_2 += 1
                    continue
                if hyp((x_2 - z.NextCenter[0]), (y_2 - z.NextCenter[1])) > (z.NextRadius - 15):
                    i_2 += 1
                    continue
                nk = b.Nav.Index(x_2, y_2)
                if b.Nav.Solid[nk]:
                    i_2 += 1
                    continue
                until, banned = b.banUntil.get((-((k + 1))), 0.0), (-((k + 1))) in b.banUntil
                if banned and (b.t < until):
                    i_2 += 1
                    continue
                if not b.reachable(x_2, y_2):
                    b.seenT[k] = go_f32(b.t)
                    i_2 += 1
                    continue
                d = hyp((x_2 - b.pos[0]), (y_2 - b.pos[1]))
                s = d - (min(age, 300) * 0.15)
                if s < bs:
                    best, bs = k, s
                i_2 += 1
            j_2 += 1
        if best < 0:
            return 0, 0, False
        b.roamCell, b.roamT = best, b.t
        i_3, j_3 = go_remainder(best, b.seenNX), go_intdiv(best, b.seenNX)
        x_3, y_3 = (b.W.MinX + (((float(i_3) + 0.5)) * seenCell)), (
            b.W.MinY + (((float(j_3) + 0.5)) * seenCell)
        )
        c_2 = b.Nav.Nearest(x_3, y_3, (b.radius + 0.3), b.height, 8)
        if c_2 >= 0:
            px_2, py_2 = b.Nav.Pos(c_2)
            return px_2, py_2, True
        b.seenT[best] = go_f32(b.t)
        return 0, 0, False

    def navCost(b):
        # navCost is the extra per-cell path cost: keep inside the zone, and (in stealth) keep out of the open.
        z = b.o.Zone
        cx, cy, r = z.Center[0], z.Center[1], z.Radius
        stealth = b.st.stealth
        exp = None
        if stealth:
            exp = b.Nav.Exposure()

        def _tmp_103(k_2):
            x, y = b.Nav.Pos(k_2)
            c = go_f32(0)
            if hyp((x - cx), (y - cy)) > (r - 3):
                c += 6
            if stealth:
                e = exp.At(k_2)
                if e <= 1:
                    c += go_f32((e * 2.5))
            return c

        return _tmp_103

    def think(b, act):
        # think is the per-decision policy.
        b.pickUpgrade(act)
        b.manageWeapons(act)
        st = b.belief()
        b.st = copy(st)
        if go_remainder(b.o.Tick, 6) == 0:
            b.markSeen()
        zi = b.zoneInfo()
        ths = b.assess()
        inc = b.gatherIncoming()
        hpFrac = go_div(b.hp, b.maxHP)
        tgt = None
        bestS = -1.0
        engagedDPS = 0.0
        nEngaged = 0
        for i in range(len(ths)):
            th = ths[i]
            if th.engaged:
                engagedDPS += th.dps
                nEngaged += 1
            if not th.tr.Listed:
                continue
            s = go_div(1, ((1 + (th.d / 60))))
            if th.tr.LOS:
                s *= 3
            if th.engaged:
                s *= 1.6
            if th.tr.MaxHP > 0:
                s *= 1 + ((1 - go_div(th.tr.HP, th.tr.MaxHP)))
            if th.tr.ID == b.targetID:
                s *= 1.2
            if (b.P.RearBonus > 0) and b.isRear(th.tr):
                s *= 1 + b.P.RearBonus
            if (((b.P.CookoffBonus > 0) and (b.has("laser") >= 0)) and th.tr.Mortar) and (
                stat(b.C.Weapons.get("laser", {}), "cookoff", 0) > 0
            ):
                s *= 1 + b.P.CookoffBonus
            if b.P.ThreatFocus:
                if th.tr.Light and (th.d < (stat(b.C.Weapons.get("lightning", {}), "range", 45) + 35)):
                    s *= 1.25
                elif th.tr.Laser:
                    s *= 1.18
                if ((th.tr.MaxHP > 0) and (th.tr.HP > 0)) and (go_div(th.tr.HP, th.tr.MaxHP) < 0.35):
                    s *= 1.25
            if s > bestS:
                bestS, tgt = s, th
        if tgt is not None:
            b.targetID = tgt.tr.ID
        else:
            b.targetID = -1
        watchers = b.seenBy(ths, 230)
        underFire = (b.t - b.lastWeaponDT) < 3.0
        danger = (nEngaged > 0) or underFire
        overall = 10.0
        if engagedDPS > 1:
            mine = 1.0
            if tgt is not None:
                mine = b.myDPS(tgt.d)
            need = 0.0
            for i_2 in range(len(ths)):
                if ths[i_2].engaged:
                    need += go_div(max(ths[i_2].tr.HP, 20), max(mine, 1))
            overall = go_div((go_div(b.hp, ((engagedDPS * ((1 - b.armor)))))), max(need, 0.1))
            if ((nEngaged == 1) and (tgt is not None)) and tgt.engaged:
                overall = tgt.adv
        if (st.stealth and (tgt is not None)) and tgt.engaged:
            f = clamp((((tgt.d - 60)) / 60), 0, 1)
            st.disengage = b.P.CloseDisengage + (((st.disengage - b.P.CloseDisengage)) * f)
        visibleFoe = (((tgt is not None) and tgt.engaged) and tgt.tr.LOS) and tgt.tr.Listed
        knownFoe = ((tgt is not None) and tgt.engaged) and tgt.tr.Listed
        if b.retreating:
            healed = hpFrac >= b.P.ReturnHP
            winnable = overall > max((st.disengage * 1.25), 0.95)
            if healed and (((not danger) or winnable)):
                b.retreating = False
            elif (not danger) and (hpFrac >= (b.P.ReturnHP - 0.1)):
                b.retreating = False
            elif ((winnable and (hpFrac > 0.3)) and (nEngaged <= 1)) and knownFoe:
                b.retreating = False
            elif (((visibleFoe and (tgt.d < 45)) and ((b.t - b.retreatT) > 2.0)) and (nEngaged <= 1)) and (
                overall > 0.35
            ):
                b.retreating = False
                b.corneredT = b.t
            elif (
                (((b.P.RetreatRunMax > 0) and st.avoid) and visibleFoe) and ((b.t - b.retreatT) > 0.5)
            ) and (not b.coverClose(ths, tgt)):
                b.retreating = False
                b.corneredT = b.t
                b.standT = b.t
        elif danger and ((b.t - b.corneredT) > 4):
            leave = False
            phantoms = 0
            for i_3 in range(len(ths)):
                if ths[i_3].phantom:
                    phantoms += 1
            dmgRate = b.recentDmg / 3.0
            ttd = go_div(b.hp, max(dmgRate, 1))
            if (nEngaged <= 1) and knownFoe:
                leave = ((overall < b.P.DuelDisengage) and (tgt.d > 30)) and (ttd < 25)
            elif nEngaged >= 2:
                leave = (((ttd < b.P.LeaveTTD) and (hpFrac < 0.8))) or (
                    ((hpFrac < b.P.RetreatHP) and (ttd < (2 * b.P.LeaveTTD)))
                )
            else:
                leave = (underFire and (phantoms > 0)) and (((ttd < (1.5 * b.P.LeaveTTD)) or (hpFrac < 0.6)))
            if (((leave and (b.P.RetreatRunMax > 0)) and st.avoid) and visibleFoe) and (
                not b.coverClose(ths, tgt)
            ):
                leave = False
                b.standT = b.t
            if leave:
                b.retreating = True
                b.retreatT = b.t
                b.coverCell = -1
        if (
            ((((tgt is not None) and tgt.tr.LOS) and tgt.tr.Listed) and (tgt.tr.HP > 0))
            and (tgt.tr.HP < ((b.myDPS(tgt.d) * 1.2) + 40))
        ) and (hpFrac > 0.12):
            b.retreating = False
        patient = (((st.name == "squad") and (b.P.PatientSecs > 0)) and (b.t < b.P.PatientSecs)) and (
            b.o.Self.Cubes < b.P.PatientCubes
        )
        wantFight = False
        slip = False
        plink = False
        unprovoked = False
        roofDuck = False
        fightWhy = ""
        onRoof = (b.onRoof() >= 0) and b.o.Self.Grounded
        roofWanted = b.roofWanted(st, zi)
        huntR = b.P.HuntRange
        if (b.has("laser") >= 0) and (b.P.HuntRangeLaser > huntR):
            huntR = b.P.HuntRangeLaser
        if (tgt is not None) and (not b.retreating):
            if ((patient and (nEngaged <= 1)) and (tgt.d > b.P.PatientRange)) and (hpFrac > 0.55):
                pass
            elif tgt.engaged:
                if st.stealth:
                    if (tgt.d < b.P.StealthFightRange) or (tgt.adv >= st.engageRatio):
                        wantFight = True
                elif st.avoid:
                    provoked = (
                        (((not b.P.ProvokeRule) or ((b.t - tgt.tr.HurtMeT) < 4)) or (tgt.d < b.P.AvoidRange))
                        or (((tgt.tr.Laser and tgt.tr.Charging) and ((b.t - tgt.tr.AimAtMeT) < 0.4)))
                    ) or (
                        (
                            ((b.P.LaserPreempt and tgt.tr.Laser) and tgt.tr.LOS)
                            and ((b.t - tgt.tr.AimAtMeT) < 0.6)
                        )
                    )
                    far = (tgt.d >= b.P.AvoidRange) and (tgt.adv < b.P.AvoidAdv)
                    heavy = ((tgt.tr.Laser or ((b.recentDmg / 3.0) > b.P.PlinkMaxDPS)) or (hpFrac < 0.5)) or (
                        nEngaged >= 2
                    )
                    edgeThr, edgeBig = b.P.AvoidAdv, b.P.CoverEdgeAdv
                    if b.P.EdgeHold > 0:
                        if (b.t - b.edgeOnT) < b.P.EdgeHold:
                            edgeThr, edgeBig = (edgeThr * 0.75), (edgeBig * 0.75)
                        elif (b.t - b.slipOnT) < b.P.EdgeHold:
                            edgeThr, edgeBig = (edgeThr * 1.3), (edgeBig * 1.3)
                    edge = ((b.laserEdge(tgt.tr) and (tgt.adv >= edgeThr))) or (tgt.adv >= edgeBig)
                    if edge and provoked:
                        b.edgeOnT = b.t
                    coverFirst = ((b.P.CoverFirst and provoked) and (not edge)) and (
                        tgt.d >= b.P.CoverMinRange
                    )
                    if not provoked:
                        unprovoked = True
                    elif (coverFirst and (not ((onRoof and roofWanted)))) and b.slipFromX(tgt, ths, True):
                        slip = True
                    elif (onRoof and roofWanted) and (not b.enemyOnRoof(ths)):
                        roofDuck = True
                    elif (far and heavy) and b.slipFrom(tgt, ths):
                        slip = True
                    elif (far and (not heavy)) and (b.P.PlinkMaxDPS > 0):
                        plink = True
                    elif far and b.slipFrom(tgt, ths):
                        slip = True
                    else:
                        wantFight = True
                        if tgt.adv >= b.P.AvoidAdv:
                            fightWhy = ".edge"
                        elif (tgt.d < b.P.AvoidRange) and (
                            not ((b.P.CoverFirst and (tgt.d >= b.P.CoverMinRange)))
                        ):
                            fightWhy = ".close"
                        else:
                            fightWhy = ".nocover"
                        if (b.t - b.standT) < 1.0:
                            fightWhy = ".stand"
                else:
                    wantFight = True
            elif (
                (((st.hunt and (tgt.adv >= st.engageRatio)) and (tgt.d < huntR)) and tgt.tr.LOS)
                and (hpFrac > 0.6)
            ) and (
                (
                    (((not b.P.HuntLaserEdge) or (not st.avoid)) or b.laserEdge(tgt.tr))
                    or (tgt.adv >= b.P.CoverEdgeAdv)
                )
            ):
                wantFight = True
                fightWhy = ".hunt"
            elif (st.name == "duel") and (hpFrac > 0.5):
                wantFight = True
            elif (
                ((st.stealth and tgt.tr.LOS) and (tgt.d < 85)) and (tgt.tr.HP < (0.25 * max(tgt.tr.MaxHP, 1)))
            ) and (tgt.adv > 1.5):
                wantFight = True
        peek = False
        peekLi = b.has("laser")
        if (
            (
                (
                    (
                        (
                            (
                                ((b.P.Peek and ((st.avoid or b.P.SquadPeek))) and (peekLi >= 0))
                                and (tgt is not None)
                            )
                            and (not b.retreating)
                        )
                        and tgt.tr.Listed
                    )
                    and (not tgt.tr.NPC)
                )
                and (((wantFight or slip) or roofDuck))
            )
            and (tgt.d > b.P.PeekMinRange)
        ) and (tgt.d < 272):
            roofID = -1
            if onRoof and roofWanted:
                roofID = b.onRoof()
            if b.peekPlanFor(tgt, ths, roofID):
                peek = True
                wantFight, slip, roofDuck = False, False, False
        if plink and (b.chooseLoot(True, st) is None):
            plink = False
            if b.slipFrom(tgt, ths):
                slip = True
            else:
                wantFight = True
        quiet = (go_len(watchers) == 0) and (not danger)
        if quiet:
            for i_4 in range(len(ths)):
                if ((b.t - ths[i_4].tr.LastSeen) < 6) and (ths[i_4].d < 180):
                    quiet = False
                    break
        if not quiet:
            b.unquietT = b.t
        elif (b.t - b.unquietT) < b.P.QuietHoldS:
            quiet = False
        rq = steerReq(threats=inc)
        li = b.has("laser")
        if (li >= 0) and (b.slots[li].charge > 0):
            rq.slow = True
        laserThreatNow = False
        for i_5 in range(len(ths)):
            tr = ths[i_5].tr
            if ((not tr.Laser) or (not tr.Charging)) or (not tr.LOS):
                continue
            aimMatch = (b.t - tr.AimAtMeT) < 0.25
            if b.P.LaserDodgeV2 and (not aimMatch):
                bear = math.atan2((b.pos[1] - tr.Pos[1]), (b.pos[0] - tr.Pos[0]))
                off = abs(angDiff(tr.Aim[0], bear))
                aimMatch = ((b.t - tr.AimAtMeT) < 0.55) or (off < 0.42)
            if aimMatch:
                laserThreatNow = True
                sc = tr.scale(b.sizePerCube)
                ex, ey, ez = tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (7 * sc))
                dmg = (stat(b.C.Weapons.get("laser", {}), "damage", 315) * b.cubeDamageMul(tr.Cubes)) * 0.85
                if b.has("mortar") >= 0:
                    dmg *= 1 + stat(b.C.Weapons.get("laser", {}), "cookoff", 0)
                aimCos, aimSin = math.cos(tr.Aim[0]), math.sin(tr.Aim[0])
                beamW = b.P.LaserBeamW
                beamHalf = b.radius + 3.0
                lasRange = stat(b.C.Weapons.get("laser", {}), "range", 280)
                prev = rq.posCost

                def _tmp_116(
                    x,
                    y,
                    aimCos=aimCos,
                    aimSin=aimSin,
                    beamHalf=beamHalf,
                    beamW=beamW,
                    dmg=dmg,
                    ex=ex,
                    ey=ey,
                    ez=ez,
                    lasRange=lasRange,
                    prev=prev,
                ):
                    c = 0.0
                    if prev is not None:
                        c = prev(x, y)
                    if b.W.Visible(ex, ey, ez, x, y, (b.pos[2] + (b.height * 0.5))) or b.W.Visible(
                        ex, ey, ez, x, y, (b.pos[2] + (b.height * 0.9))
                    ):
                        c += dmg
                        if b.P.LaserDodgeV2 and (beamW > 0):
                            bx, by = (ex + (aimCos * lasRange)), (ey + (aimSin * lasRange))
                            perp, _ = segPointDist2D(x, y, ex, ey, bx, by)
                            if perp < (beamHalf * 2.5):
                                c += beamW * ((1 - go_div(perp, ((beamHalf * 2.5)))))
                    return c

                rq.posCost = _tmp_116
                rq.lookTicks = 12
                rq.dodgeBoost = True
        if (
            (
                (((b.P.SquadLaserCover and laserThreatNow) and (not st.avoid)) and (not b.retreating))
                and (not peek)
            )
            and (not slip)
        ) and (not ((onRoof and roofWanted))):
            finishSoon = (((tgt is not None) and tgt.tr.LOS) and (tgt.tr.HP > 0)) and (
                tgt.tr.HP < ((b.myDPS(tgt.d) * 1.1) + 40)
            )
            if not finishSoon:
                c_2 = b.findCover(ths, 24)
                if c_2 >= 0:
                    b.slipCell = c_2
                    b.slipT = b.t
                    b.slipOnT = b.t
                    slip = True
                    wantFight = False
        if b.P.AntiLightningW > 0:
            haveLight = (b.has("lightning") >= 0) and (b.energy > 18)
            if (not haveLight) or (hpFrac < 0.55):
                lightBase = stat(b.C.Weapons.get("lightning", {}), "range", 45)
                pad = b.P.AntiLightningPad
                if pad <= 0:
                    pad = 10
                for i_6 in range(len(ths)):
                    tr_2 = ths[i_6].tr
                    if (not tr_2.Light) or (((not tr_2.Listed) and ((b.t - tr_2.LastSeen) > 2.5))):
                        continue
                    safeR = lightBase + pad
                    if tr_2.Cubes >= 6:
                        safeR += 6
                    if ths[i_6].d > (safeR + 22):
                        continue
                    lx, ly = tr_2.Pos[0], tr_2.Pos[1]
                    w = b.P.AntiLightningW
                    prev_2 = rq.posCost

                    def _tmp_118(x_2, y_2, lx=lx, ly=ly, prev_2=prev_2, safeR=safeR, w=w):
                        c_3 = 0.0
                        if prev_2 is not None:
                            c_3 = prev_2(x_2, y_2)
                        d = hyp((x_2 - lx), (y_2 - ly))
                        if d < safeR:
                            f_2 = go_div(((safeR - d)), safeR)
                            c_3 += (w * f_2) * ((1 + (((safeR - d)) / 20)))
                        return c_3

                    rq.posCost = _tmp_118
                    if (ths[i_6].d < (safeR + 4)) and tr_2.LOS:
                        rq.dodgeBoost = True
                        if rq.lookTicks < 10:
                            rq.lookTicks = 10
        heading, haveHeading = 0.0, False
        shootItem = None
        shootHP = 0.0
        goalOK = True
        navigating = False
        lastGoal = [0.0] * 2

        def _tmp_119(gx, gy, w_2, boost):
            nonlocal goalOK
            nonlocal haveHeading
            nonlocal heading
            nonlocal lastGoal
            nonlocal navigating
            dx, dy, d_2, ok = b.navDir(gx, gy)
            goalOK = ok
            navigating = True
            lastGoal = [gx, gy]
            rq.wantX, rq.wantY, rq.wantW, rq.boost = dx, dy, w_2, boost
            if (dx != 0) or (dy != 0):
                heading, haveHeading = math.atan2(dy, dx), True
            return d_2

        setGoal = _tmp_119
        holdFire = False
        peekCharge = False
        direct = False
        b.holdClimb = st.avoid and (((go_len(watchers) > 0) or underFire))
        if st.avoid and (not b.holdClimb):
            for i_7 in range(len(ths)):
                if (ths[i_7].tr.Listed and ths[i_7].tr.LOS) and (ths[i_7].d < b.P.ClimbClearRange):
                    b.holdClimb = True
                    break
        b.holdRoofMove = (
            ((((b.P.RoofLeaveQuiet > 0) and st.avoid) and onRoof) and (((go_len(watchers) > 0) or underFire)))
            and (zi.tPass > b.P.RoofLeaveQuiet)
        ) and (not zi.urgent)
        roofCoverCell = -1
        wantRoofCover = st.stealth and (
            (((b.retreating or wantFight) or (go_len(watchers) > 0)) or underFire)
        )
        if st.avoid and ((((roofDuck or b.retreating) or (go_len(watchers) > 0)) or underFire)):
            wantRoofCover = True
            b.roofCoverHoldT = b.t
        elif st.avoid and ((b.t - b.roofCoverHoldT) < b.P.RoofCoverHold):
            wantRoofCover = True
        if ((onRoof and roofWanted) and wantRoofCover) and (not b.enemyOnRoof(ths)):
            if (b.t - b.roofCoverT) > 0.4:
                b.roofCoverC = b.roofCover(b.onRoof(), ths)
                b.roofCoverT = b.t
            roofCoverCell = b.roofCoverC
        else:
            b.roofCoverC = -1
            b.roofCoverT = -100
        if (roofDuck and (roofCoverCell < 0)) and (not b.retreating):
            wantFight = True
        if ((b.roofFirstOK and (not b.roofFirstChecked)) and (b.P.RoofFirstSecs > 0)) and roofWanted:
            b.roofFirstChecked = True
            _, acc, ok_2 = b.chooseRoof()
            if ok_2:
                gx_2, gy_2 = b.Nav.Pos(acc.Ground)
                ok_2 = hyp((gx_2 - b.pos[0]), (gy_2 - b.pos[1])) <= b.P.RoofFirstDist
            b.roofFirstOK = ok_2
        roofFirst = (
            ((roofWanted and (not onRoof)) and (b.t < b.P.RoofFirstSecs)) and b.roofFirstOK
        ) and b.roofFirstChecked
        shy = False
        shyLoot = None
        if (
            ((((b.shyPhase(st) and (not wantFight)) and (not slip)) and (not peek)) and (not roofDuck))
            and (not b.retreating)
        ) and (not onRoof):
            shy = b.exposedTo(b.P.ShyMem, b.P.ShyRange)
            if shy:
                shyLoot = b.chooseLoot(False, st)
                if (shyLoot is not None) and (dist2(b.pos, shyLoot.pos) <= 60):
                    shy = False
        if (b.roof.state == roofApproach) and ((b.t - b.roof.stepT) > 2.5):
            b.roof.state = roofNone
        try:
            if (zi.critical or ((zi.urgent and ((((not wantFight) or (tgt is None)) or (tgt.d > 60)))))) or (
                (zi.urgent and (zi.tPass < 5))
            ):
                b.mode = "zone"
                b.roof.state = roofNone
                if (b.P.ZoneSlack > 0) and (b.lootID >= 0):
                    b.banUntil[b.lootID] = b.t + 20
                    b.lootID = -1
                setGoal(zi.goal[0], zi.goal[1], 3.0, (zi.critical and (b.energy > 15)))
                rq.zoneFree = True
                if not zi.walkable:
                    b.mode = "zone-over"
                    b.overland(act, zi.goal[0], zi.goal[1])
                    direct = True
            elif b.roof.state == roofClimb:
                b.mode = "climb"
                b.roofClimbStep(act)
                direct = True
            elif peek:
                b.mode = "peek"
                cell, charge = b.peekStep(ths, peekLi, hpFrac)
                peekCharge = charge
                gx_3, gy_3 = b.Nav.Pos(cell)
                d_3 = setGoal(gx_3, gy_3, 2.6, False)
                if d_3 < 1.0:
                    rq.wantW = 0
                    rq.hold = True
                rq.fenceRoof = onRoof and roofWanted
            elif roofCoverCell >= 0:
                b.mode = "roof-cover"
                x_3, y_3 = b.Nav.Pos(roofCoverCell)
                d_4 = setGoal(x_3, y_3, 2.4, False)
                if d_4 < 1.8:
                    rq.wantW = 0
                    rq.hold = True
                rq.fenceRoof = True
                holdFire = ((tgt is None) or (not tgt.engaged)) or (tgt.d > b.P.FFAReturnFire)
            elif slip:
                b.mode = "slip"
                deepSlip = (
                    (((b.P.CoverMargin > 0) and (b.deepCell >= 0)) and ((b.t - b.deepT) < 8))
                    and ((b.t - b.lastWeaponDT) > 0.45)
                ) and b.cellHidden(b.deepCell, ths)
                if not deepSlip:
                    b.deepCell = -1
                if deepSlip:
                    cx, cy = b.Nav.Pos(b.deepCell)
                    d_5 = setGoal(cx, cy, 2.5, False)
                    if (d_5 < 1.5) or (not goalOK):
                        rq.wantW = 0
                        rq.hold = True
                        b.mode = "ambush"
                else:
                    cx_2, cy_2 = b.Nav.Pos(b.slipCell)
                    d_6 = setGoal(cx_2, cy_2, 2.5, ((b.energy > 25) and underFire))
                    if (d_6 < 0.9) or (((d_6 < 3.0) and b.hiddenHere(ths))):
                        if (b.P.CoverMargin > 0) and ((b.t - b.deepTryT) > 0.6):
                            b.deepTryT = b.t
                            c_4 = b.deeperCover(ths, 45, False)
                            if c_4 >= 0:
                                b.deepCell, b.deepT = c_4, b.t
                        if b.deepCell >= 0:
                            cx_2, cy_2 = b.Nav.Pos(b.deepCell)
                            setGoal(cx_2, cy_2, 2.5, False)
                        else:
                            rq.wantW = 0
                            rq.hold = True
                            b.mode = "ambush"
            elif b.retreating:
                b.mode = "retreat"
                deeper = (((b.P.RunOnRange > 0) or (b.P.CoverMargin > 0))) and st.avoid
                deep = (deeper and (b.deepCell >= 0)) and ((b.t - b.deepT) < 8)
                if deep and ((((b.t - b.lastWeaponDT) < 0.45) or (not b.cellHidden(b.deepCell, ths)))):
                    deep = False
                if not deep:
                    b.deepCell = -1
                    if (b.t - b.coverT) > 0.5:
                        b.coverCell = b.findCover(ths, 90)
                        b.coverT = b.t
                if deep:
                    b.mode = "retreat-on"
                    cx_3, cy_3 = b.Nav.Pos(b.deepCell)
                    d_7 = setGoal(cx_3, cy_3, 2.5, ((b.energy > 35) and (b.nearestEye(ths) < 60)))
                    if (d_7 < 1.5) or (not goalOK):
                        b.deepCell = -1
                        b.coverT = -100
                elif b.coverCell >= 0:
                    cx_4, cy_4 = b.Nav.Pos(b.coverCell)
                    d_8 = setGoal(cx_4, cy_4, 2.5, ((b.energy > 20) and underFire))
                    if (d_8 < 0.9) or (((d_8 < 3.0) and b.hiddenHere(ths))):
                        if deeper and ((b.t - b.deepTryT) > 0.6):
                            b.deepTryT = b.t
                            c_5 = b.deeperCover(ths, 75, True)
                            if c_5 >= 0:
                                b.deepCell, b.deepT = c_5, b.t
                        if b.deepCell >= 0:
                            b.mode = "retreat-on"
                            cx_4, cy_4 = b.Nav.Pos(b.deepCell)
                            setGoal(cx_4, cy_4, 2.5, ((b.energy > 35) and (b.nearestEye(ths) < 60)))
                        else:
                            rq.wantW = 0
                            rq.hold = True
                            b.mode = "heal"
                else:
                    from_ = b.fleeFrom(tgt, ths)
                    if from_ is not None:
                        dx_2, dy_2 = norm2((b.pos[0] - from_.tr.Pos[0]), (b.pos[1] - from_.tr.Pos[1]))
                        gx_4, gy_4 = (b.pos[0] + (dx_2 * 30)), (b.pos[1] + (dy_2 * 30))
                        setGoal(gx_4, gy_4, 2.0, (b.energy > 30))
                    elif (
                        (((b.P.CoverMargin > 0) and st.avoid) and (zi.outNext < (-5)))
                        and ((b.t - b.lastNpcDT) > 4)
                    ) and ((b.t - b.lastWeaponDT) < 30):
                        rq.wantW = 0
                        rq.hold = True
                        b.mode = "heal"
                    else:
                        setGoal(zi.goal[0], zi.goal[1], 1.5, False)
                if (st.stealth and (tgt is not None)) and (tgt.d > b.P.FFAReturnFire):
                    holdFire = True
            elif wantFight:
                b.mode = "fight" + fightWhy
                w_3 = b.weaponRun(32)
                if (w_3 is not None) and (not onRoof):
                    b.mode = "fight+arm"
                    dx_3, dy_3, _, _ = b.navDir(w_3.Pos[0], w_3.Pos[1])
                    rq.wantX, rq.wantY, rq.wantW = dx_3, dy_3, 2.4
                else:
                    c_6 = b.cubeRun(tgt, st, hpFrac)
                    if c_6 is not None:
                        b.mode = "fight+cube"
                        dx_4, dy_4, _, _ = b.navDir(c_6.Pos[0], c_6.Pos[1])
                        rq.wantX, rq.wantY, rq.wantW = dx_4, dy_4, 2.2
                    else:
                        near = b.kiteFrom(ths, nEngaged)
                        if near is not None:
                            b.mode = "kite"
                            b.strafe(rq, near.tr.Pos, b.P.KiteMin, b.P.KiteMax, 2.0)
                            if (near.d < 70) and (b.energy > 45):
                                rq.boost = True
                        else:
                            b.fightMove(rq, tgt)
                rq.fenceRoof = onRoof and roofWanted
            elif shy:
                b.mode = "shy"
                if (b.t - b.evadeT) > 0.6:
                    b.evadeCell = b.findCover(ths, 110)
                    b.evadeT = b.t
                if b.evadeCell >= 0:
                    cx_5, cy_5 = b.Nav.Pos(b.evadeCell)
                    d_9 = setGoal(cx_5, cy_5, 2.2, ((b.P.ShyBoost > 0) and (b.energy > b.P.ShyBoost)))
                    if (d_9 < 0.9) or (((d_9 < 3.0) and b.hiddenHere(ths))):
                        rq.wantW = 0
                        rq.hold = True
                elif shyLoot is not None:
                    setGoal(shyLoot.pos[0], shyLoot.pos[1], 2.0, False)
                else:
                    nearest = None
                    for i_8 in range(len(ths)):
                        tr_3 = ths[i_8].tr
                        if ((b.t - tr_3.LastSeen) <= b.P.ShyMem) and (
                            ((nearest is None) or (ths[i_8].d < nearest.d))
                        ):
                            nearest = ths[i_8]
                    if nearest is not None:
                        dx_5, dy_5 = norm2((b.pos[0] - nearest.tr.Pos[0]), (b.pos[1] - nearest.tr.Pos[1]))
                        setGoal((b.pos[0] + (dx_5 * 40)), (b.pos[1] + (dy_5 * 40)), 2.0, False)
                holdFire = True
            elif (b.pest() is not None) and (((not st.stealth) or (go_len(watchers) == 0))):
                tr_4 = b.pest()
                b.mode = "pest"
                at = b.targetOf(tr_4)
                d_10 = dist2(b.pos, tr_4.Pos)
                if tr_4.LOS and (d_10 < 120):
                    shootItem = at
                    shootHP = tr_4.HP
                    b.strafe(rq, tr_4.Pos, 35, 60, 1.0)
                else:
                    setGoal(tr_4.Pos[0], tr_4.Pos[1], 1.5, False)
            elif (((st.stealth and (nEngaged == 0)) and (not onRoof)) and (not roofFirst)) and (
                b.weaponRun(b.P.ArmRadius) is not None
            ):
                w_4 = b.weaponRun(b.P.ArmRadius)
                b.mode = "arm"
                setGoal(w_4.Pos[0], w_4.Pos[1], 2.2, False)
                if not goalOK:
                    b.banUntil[w_4.ID] = b.t + 40
                holdFire = True
            elif ((st.stealth and (go_len(watchers) > 0)) and (not ((onRoof and roofWanted)))) and (
                b.roof.state != roofApproach
            ):
                b.mode = "evade"
                if (b.t - b.evadeT) > 0.6:
                    b.evadeCell = b.findCover(ths, 110)
                    b.evadeT = b.t
                if b.evadeCell >= 0:
                    cx_6, cy_6 = b.Nav.Pos(b.evadeCell)
                    d_11 = setGoal(cx_6, cy_6, 2.2, False)
                    if (d_11 < 0.9) or (((d_11 < 3.0) and b.hiddenHere(ths))):
                        rq.wantW = 0
                        rq.hold = True
                else:
                    w_5 = watchers[0]
                    dx_6, dy_6 = norm2((b.pos[0] - w_5.tr.Pos[0]), (b.pos[1] - w_5.tr.Pos[1]))
                    setGoal((b.pos[0] + (dx_6 * 40)), (b.pos[1] + (dy_6 * 40)), 1.8, False)
                holdFire = ((tgt is None) or (not tgt.engaged)) or (tgt.d > b.P.FFAReturnFire)
            else:
                if (
                    (
                        (((b.P.RegenHoldHP > 0) and (not danger)) and (hpFrac < b.P.RegenHoldHP))
                        and ((b.t - b.lastWeaponDT) < 16)
                    )
                    and ((b.t - b.lastNpcDT) > 3)
                ) and (zi.outNext < (-5)):
                    b.mode = "regen-hold"
                    rq.wantW = 0
                    rq.hold = True
                    raise StopIteration("_tmp_121break")
                if patient:
                    holdFire = True
                l = None
                if (((not st.stealth) or quiet)) and (not roofFirst):
                    l = b.chooseLoot((danger and (not patient)), st)
                if ((((l is not None) and onRoof) and roofWanted) and (l.kind != "drop")) and (
                    not ((((l.kind == "pickup") and (b.has("laser") < 0)) and (dist2(b.pos, l.pos) < 90)))
                ):
                    l = None
                if l is not None:
                    b.mode = "loot:" + l.kind
                    b.lootID = l.id_
                    d_12 = dist2(b.pos, l.pos)
                    _tmp_124 = l.kind
                    if _tmp_124 == "crate":
                        it = b.crates.get(l.id_, None)
                        at_2 = aimTarget(
                            pos=l.pos,
                            radius=stat(b.C.Crates, "radius", 1.4),
                            centerZ=(stat(b.C.Crates, "height", 2.4) * 0.5),
                        )
                        vis = (d_12 < 70) and b.W.Visible(
                            b.pos[0],
                            b.pos[1],
                            (b.pos[2] + b.muzzleH),
                            at_2.pos[0],
                            at_2.pos[1],
                            (at_2.pos[2] + at_2.centerZ),
                        )
                        if vis:
                            shootItem = at_2
                            if it is not None:
                                shootHP = it.HP
                        if (d_12 > 9) or (not vis):
                            setGoal(l.pos[0], l.pos[1], 1.5, False)
                        else:
                            rq.hold = True
                    elif _tmp_124 == "npc":
                        tr_5 = b.tracks.get(l.id_, None)
                        if tr_5 is not None:
                            at_3 = b.targetOf(tr_5)
                            if tr_5.LOS and (d_12 < 110):
                                shootItem = at_3
                                shootHP = tr_5.HP
                            if (d_12 > 60) or (not tr_5.LOS):
                                setGoal(l.pos[0], l.pos[1], 1.5, False)
                            else:
                                b.strafe(rq, tr_5.Pos, 50, 70, 1.0)
                    elif _tmp_124 == "drop":
                        if d_12 > 3:
                            setGoal(l.pos[0], l.pos[1], 2.0, False)
                        else:
                            rq.hold = True
                    else:
                        sprint = False
                        if (
                            ((l.kind == "pickup") and (b.P.LootBoost > 0)) and (b.energy > b.P.LootBoost)
                        ) and (d_12 > 25):
                            it_2 = b.pickups.get(l.id_, None)
                            if ((it_2 is not None) and (it_2.Kind == "laser")) and (b.has("laser") < 0):
                                sprint = True
                        setGoal(l.pos[0], l.pos[1], 2.0, sprint)
                    if navigating and (not goalOK):
                        b.banUntil[l.id_] = b.t + 40
                else:
                    b.lootID = -1
                    b.mode = "hold"
                    if (b.shyPhase(st) and (not onRoof)) and b.mechSeenWithin(b.P.ShyMem):
                        b.mode = "lie-low"
                        rq.wantW = 0
                        rq.hold = True
                    elif zi.final:
                        tol = 2.0
                        boostFinal = False
                        if b.P.FinalHold:
                            tol = clamp((b.o.Zone.Radius * 0.06), 0.35, 2.0)
                            boostFinal = (b.o.Zone.Radius < 18) and (b.energy > 15)
                        d_13 = setGoal(b.o.Zone.NextCenter[0], b.o.Zone.NextCenter[1], 1.8, boostFinal)
                        if d_13 < tol:
                            rq.wantW = 0
                            rq.hold = True
                    else:
                        rx, ry, ok_3 = b.roamTarget(st, hpFrac)
                        if (ok_3 and (not roofFirst)) and (
                            ((not roofWanted) or (((not b.armed()) and quiet)))
                        ):
                            b.mode = "roam"
                            setGoal(rx, ry, 1.5, False)
                            if (not goalOK) and (b.roamCell >= 0):
                                b.banUntil[(-((b.roamCell + 1)))] = b.t + 120
                                b.roamCell = -1
                        else:
                            ho, ok_4 = b.hideoutFor(st, zi, roofWanted)
                            if ok_4 and (ho.class_ != hmRoof):
                                b.mode = "hide"
                                b.roof.state, b.roof.want, b.roof.spot = roofNone, (-1), (-1)
                                gx_5, gy_5 = b.Nav.Pos(ho.cell)
                                d_14 = setGoal(gx_5, gy_5, 1.5, False)
                                if d_14 < 2.5:
                                    rq.wantW = 0
                                    rq.hold = True
                            else:
                                gx_6, gy_6, settled, ok2 = b.roofPlanStep(roofWanted, act)
                                if ok2:
                                    b.mode = "roof"
                                    if settled:
                                        rq.hold = True
                                    else:
                                        setGoal(gx_6, gy_6, 1.6, False)
                                    rq.fenceRoof = onRoof and (b.roof.state == roofOn)
                                else:
                                    if (b.holdCell < 0) or ((b.t - b.hideT) > 2.0):
                                        b.holdCell = b.chooseHide(zi)
                                        b.hideT = b.t
                                    gx_7, gy_7 = zi.goal[0], zi.goal[1]
                                    if b.holdCell >= 0:
                                        gx_7, gy_7 = b.Nav.Pos(b.holdCell)
                                    d_15 = setGoal(gx_7, gy_7, 1.4, False)
                                    if d_15 < 2.5:
                                        rq.wantW = 0
                                        rq.hold = True
        except StopIteration as _go_flow:
            if _go_flow.args != ("_tmp_121break",):
                raise
        if ((((not direct) and navigating) and (not rq.hold)) and (not rq.fenceRoof)) and (
            ((not b.onGroundLevel()) or (not goalOK))
        ):
            gd = hyp((lastGoal[0] - b.pos[0]), (lastGoal[1] - b.pos[1]))
            if gd > 3:
                b.overland(act, lastGoal[0], lastGoal[1])
                direct = True
        if (
            (((((b.P.Jink > 0) and (not direct)) and navigating) and (not rq.hold)) and (not rq.fenceRoof))
            and underFire
        ) and (((rq.wantX != 0) or (rq.wantY != 0))):
            far_2 = False
            for i_9 in range(len(ths)):
                if ((ths[i_9].engaged and (not ths[i_9].phantom)) and (ths[i_9].d > 55)) and (
                    (b.t - ths[i_9].tr.HurtMeT) < 3
                ):
                    far_2 = True
            gd_2 = hyp((lastGoal[0] - b.pos[0]), (lastGoal[1] - b.pos[1]))
            if far_2 and (gd_2 > 12):
                if b.t >= b.jinkT:
                    if b.rng.Float64() < 0.85:
                        b.jinkSign = -b.jinkSign
                    b.jinkT = (b.t + 0.3) + (b.rng.Float64() * 0.4)
                px, py = (-rq.wantY), rq.wantX
                rq.wantX, rq.wantY = norm2(
                    (rq.wantX + ((px * b.P.Jink) * b.jinkSign)), (rq.wantY + ((py * b.P.Jink) * b.jinkSign))
                )
        if not direct:
            b.steer(act, rq)
            b.unstick(act, ((navigating and (not rq.hold)) and (not rq.fenceRoof)))
        unseen = False
        for i_10 in range(len(ths)):
            if ths[i_10].phantom and ((b.t - ths[i_10].tr.HurtMeT) < 1.5):
                unseen = True
        if unseen and ((((tgt is None) or (not tgt.engaged)) or (not tgt.tr.LOS))):
            act.Aim = [b.lastDmgBear, 0]
            act.HasAim = True
            li_2 = b.has("laser")
            if (li_2 >= 0) and (b.slots[li_2].charge > 0):
                act.Fire[li_2] = True
        elif plink and (shootItem is not None):
            b.engage(act, shootItem, True, True, shootHP, True)
        elif (((tgt is not None) and (not holdFire)) and (not unprovoked)) and (
            (((wantFight or tgt.engaged) or b.retreating) or peek)
        ):
            at_4 = b.targetOf(tgt.tr)
            b.engage(act, at_4, tgt.tr.LOS, ((b.t - tgt.tr.LOST) < 0.8), tgt.tr.HP, True)
            if peekCharge and (peekLi >= 0):
                act.Fire[peekLi] = True
        elif shootItem is not None:
            b.engage(act, shootItem, True, True, shootHP, True)
        elif (tgt is not None) and ((tgt.tr.LOS or ((b.t - tgt.tr.LastSeen) < 3))):
            at_5 = b.targetOf(tgt.tr)
            b.engage(act, at_5, tgt.tr.LOS, False, tgt.tr.HP, False)
        else:
            b.idleAim(act, heading, haveHeading)
            gi = b.has("gun")
            if gi >= 0:
                sl = b.slots[gi]
                if (sl.reload <= 0) and (sl.ammo < (stat(sl.stats, "mag", 12) * 0.67)):
                    act.Reload = True
            li_3 = b.has("laser")
            if (li_3 >= 0) and (b.slots[li_3].charge > 0):
                _tmp_129 = b.tracks
                for _ in list(_tmp_129):
                    if _ not in _tmp_129:
                        continue
                    tr_6 = _tmp_129[_]
                    if (not tr_6.NPC) and ((b.t - tr_6.LastSeen) < 1.5):
                        act.Fire[li_3] = True
                        break
        b.modeLabel = (st.name + ":") + b.mode
        wl = ""
        i_11 = 0
        while i_11 < 2:
            if b.slots[i_11].ok:
                wl += b.slots[i_11].kind[:2]
            i_11 += 1
        td = -1.0
        if tgt is not None:
            td = tgt.d
        act.Label = go_Sprintf(
            "%s h%.0f a%d e%d k%d c%d %s d%.0f",
            b.modeLabel,
            b.hp,
            b.o.Alive,
            nEngaged,
            b.kills,
            b.o.Self.Cubes,
            wl,
            td,
        )

    def weaponRun(b, maxD):
        # weaponRun returns a weapon on the ground that is worth going for right now even with enemies about:
        # a second weapon (above all a laser) decides the early duels.
        best = None
        bv = 0.0
        _tmp_132 = b.pickups
        for _ in list(_tmp_132):
            if _ not in _tmp_132:
                continue
            it = _tmp_132[_]
            if (not it.Ground) or (not b.sameComp(it.Cell)):
                continue
            until, banned = b.banUntil.get(it.ID, 0.0), it.ID in b.banUntil
            if banned and (b.t < until):
                continue
            ok, rep = b.wantPickup(it.Kind)
            if not ok:
                continue
            v = b.weaponValue(it.Kind)
            if rep >= 0:
                v -= b.weaponValue(b.slots[rep].kind)
                if v < b.P.ArmSwapMin:
                    continue
            d = dist2(b.pos, it.Pos)
            if d > maxD:
                continue
            if not b.inFutureZone(it.Pos[0], it.Pos[1], (go_div(d, b.walk) + 2), 5):
                continue
            contested = False
            _tmp_134 = b.tracks
            for _ in list(_tmp_134):
                if _ not in _tmp_134:
                    continue
                tr = _tmp_134[_]
                if tr.NPC or ((b.t - tr.LastSeen) > 5):
                    continue
                de = dist2(tr.Pos, it.Pos)
                if (de < 30) or (de < (d * 0.8)):
                    contested = True
                    break
            if contested:
                continue
            s = go_div(v, ((d + 15)))
            if s > bv:
                best, bv = it, s
        return best

    def slipFrom(b, tgt, ths):
        # slipFrom decides whether to decline an exchange at range: true when the attacker is beyond AvoidRange,
        # we have no clear edge over it, and there is cover close by (left in b.slipCell).
        return b.slipFromX(tgt, ths, False)

    def laserEdge(b, tr):
        # laserEdge reports whether we hold a laser and this mech does not: the one situation in which, in
        # the real matches, standing to fight (or starting the fight) paid.
        return (b.has("laser") >= 0) and (not tr.Laser)

    def slipFromX(b, tgt, ths, anyEdge):
        # slipFromX is slipFrom; with anyEdge it goes for cover whatever our estimated advantage (the caller
        # has already decided this is not a fight to stand in).
        minR, maxAdv = b.P.AvoidRange, b.P.AvoidAdv
        if b.P.CoverFirst and (b.P.CoverMinRange < minR):
            minR = b.P.CoverMinRange
        if (b.t - b.slipOnT) < 1.0:
            minR, maxAdv = (minR * 0.85), (maxAdv * 1.15)
        if anyEdge:
            maxAdv = 1e9
        if ((b.P.AvoidAdv <= 0) or (tgt.d < minR)) or (tgt.adv >= maxAdv):
            return False
        if (tgt.tr.LOS and (tgt.tr.HP > 0)) and (tgt.tr.HP < ((b.myDPS(tgt.d) * 1.5) + 60)):
            return False
        if (b.t - b.slipT) > 0.5:
            reach = b.P.AvoidCover
            if tgt.tr.Laser and (b.P.AvoidCoverLaser > reach):
                reach = b.P.AvoidCoverLaser
            c = b.findCover(ths, reach)
            if ((c >= 0) or (b.P.EdgeHold <= 0)) or ((b.t - b.slipOnT) > 1.5):
                b.slipCell = c
            b.slipT = b.t
        if b.slipCell < 0:
            return False
        b.slipOnT = b.t
        return True

    def kiteFrom(b, ths, nEngaged):
        # kiteFrom returns the nearest attacker to back away from when two or more are on us (nil: do not kite).
        if (nEngaged < 2) or (b.P.KiteMin <= 0):
            return None
        if (b.P.KiteNeedsLaser and b.realModel()) and (b.has("laser") < 0):
            return None
        if ((b.has("lightning") >= 0) and (b.energy > 40)) and (b.has("laser") < 0):
            return None
        near = None
        for i in range(len(ths)):
            if ((ths[i].engaged and (not ths[i].phantom)) and ths[i].tr.Listed) and (
                ((near is None) or (ths[i].d < near.d))
            ):
                near = ths[i]
        if (near is None) or (near.d > (b.P.KiteMax + 20)):
            return None
        return near

    def armed(b):
        # armed reports whether we hold anything besides the starting gun.
        n = 0
        i = 0
        while i < 2:
            if b.slots[i].ok:
                n += 1
            i += 1
        return n >= 2

    def fleeFrom(b, tgt, ths):
        # fleeFrom is the threat to move away from: our target, else whoever is hurting us (seen or not).
        if tgt is not None:
            return tgt
        best = None
        for i in range(len(ths)):
            if ths[i].engaged and (((best is None) or (ths[i].tr.HurtMeT > best.tr.HurtMeT))):
                best = ths[i]
        return best

    def cubeRun(b, tgt, st, hpFrac):
        # cubeRun picks a cube (or pile of cubes) worth walking to in the middle of a fight.
        if b.o.Self.Cubes >= (st.wantCubes + 6):
            return None
        best = None
        bv = 0.0
        _tmp_139 = b.cubes
        for _ in list(_tmp_139):
            if _ not in _tmp_139:
                continue
            c = _tmp_139[_]
            if ((not c.Ground) or ((b.t - c.LastSeen) > 20)) or (not b.sameComp(c.Cell)):
                continue
            d = dist2(b.pos, c.Pos)
            n = 0
            _tmp_141 = b.cubes
            for _ in list(_tmp_141):
                if _ not in _tmp_141:
                    continue
                o = _tmp_141[_]
                if dist2(o.Pos, c.Pos) < 7:
                    n += 1
            maxD = 40.0
            if n >= 2:
                maxD = 110
            if st.stealth:
                maxD *= 0.5
            if (d > maxD) or (((d > 30) and (hpFrac < 0.3))):
                continue
            if b.has("lightning") < 0:
                if b.P.AntiLightningW > 0:
                    lightR = stat(b.C.Weapons.get("lightning", {}), "range", 45) + 8
                    dangerLight = False
                    _tmp_143 = b.tracks
                    for _ in list(_tmp_143):
                        if _ not in _tmp_143:
                            continue
                        tr = _tmp_143[_]
                        if (((not tr.NPC) and tr.Light) and ((b.t - tr.LastSeen) < 4)) and (
                            dist2(c.Pos, tr.Pos) < lightR
                        ):
                            dangerLight = True
                            break
                    if dangerLight:
                        continue
                elif ((tgt is not None) and tgt.tr.Light) and (dist2(c.Pos, tgt.tr.Pos) < 50):
                    continue
            if not b.inFutureZone(c.Pos[0], c.Pos[1], (go_div(d, b.walk) + 1), 3):
                continue
            v = go_div(float(n), ((d + 12)))
            if v > bv:
                best, bv = c, v
        return best

    def roamTarget(b, st, hpFrac):
        # roamTarget returns where to go exploring, when exploring is what this stance does.
        if hpFrac < 0.7:
            return 0, 0, False
        if st.stealth:
            if b.armed() or (b.t < 12):
                return 0, 0, False
            return b.roamGoal()
        if b.o.Self.Cubes >= st.wantCubes:
            return 0, 0, False
        return b.roamGoal()

    def pest(b):
        # pest returns the drone that is shooting at us (the closest one that hurt us in the last few seconds).
        if (b.t - b.lastNpcDT) > 4:
            return None
        best = None
        bd = 1e18
        _tmp_145 = b.tracks
        for _ in list(_tmp_145):
            if _ not in _tmp_145:
                continue
            tr = _tmp_145[_]
            if ((not tr.NPC) or ((b.t - tr.HurtMeT) > 4)) or ((b.t - tr.LastSeen) > 3):
                continue
            d = dist2(b.pos, tr.Pos)
            if d < bd:
                best, bd = tr, d
        return best

    def strafe(b, rq, at, rmin, rmax, w):
        # strafe circles a point while keeping the distance inside [rmin, rmax].
        if b.t >= b.strafeT:
            b.strafeSign = -b.strafeSign
            if b.rng.Float64() < 0.25:
                b.strafeSign = -b.strafeSign
            b.strafeT = (b.t + b.P.StrafeMin) + (b.rng.Float64() * ((b.P.StrafeMax - b.P.StrafeMin)))
        rx, ry = norm2((at[0] - b.pos[0]), (at[1] - b.pos[1]))
        d = dist2(b.pos, at)
        radial = 0.0
        if d > rmax:
            radial = clamp((((d - rmax)) / 15), 0, 1)
        elif d < rmin:
            radial = -clamp((((rmin - d)) / 15), 0, 1)
        tx, ty = ((-ry) * b.strafeSign), (rx * b.strafeSign)
        wx = (tx * ((1 - (0.6 * abs(radial))))) + (rx * radial)
        wy = (ty * ((1 - (0.6 * abs(radial))))) + (ry * radial)
        rq.wantX, rq.wantY = norm2(wx, wy)
        rq.wantW = w

    def fightMove(b, rq, th):
        # fightMove picks the range we want against a target and strafes there.
        tr = th.tr
        haveLight = (b.has("lightning") >= 0) and (b.energy > 18)
        rmin, rmax = th.rmin, th.rmax
        if rmax <= 0:
            rmin, rmax = 30, 55
        if not tr.LOS:
            dx, dy, _, _ = b.navDir(tr.Pos[0], tr.Pos[1])
            rq.wantX, rq.wantY, rq.wantW = dx, dy, 1.2
            return
        b.strafe(rq, tr.Pos, rmin, rmax, 1.6)
        if (haveLight and (th.d > (rmax + 10))) and (b.energy > 55):
            rq.boost = True
        if ((b.P.LightKiteBoost and (not haveLight)) and tr.Light) and (b.energy > 28):
            lr = stat(b.C.Weapons.get("lightning", {}), "range", 45)
            if th.d < (lr + 12):
                rq.boost = True

    def onRoof(b):
        # onRoof returns the id of the roof region we are standing on, or -1.
        roofs, roofOf = b.Nav.Roofs()
        k = b.Nav.Index(b.pos[0], b.pos[1])
        id_ = int(roofOf[k])
        if (id_ < 0) or (id_ >= go_len(roofs)):
            return -1
        if abs((b.pos[2] - roofs[id_].Z)) < 1.6:
            return id_
        return -1

    def maxClimb(b):
        drain = stat(b.o.Self.Stats, "jet_drain", b.mech("jet_drain", 15))
        if drain <= 0:
            drain = 15
        return go_div(((b.o.Self.MaxEnergy - 28)), drain) * 8.9

    def roofSpotOK(b, r):
        # roofSpotOK reports whether a roof's inner spot will stay inside the zone long enough to be worth it.
        z = b.o.Zone
        x, y = b.Nav.Pos(r.Inner)
        if (b.roof.want == r.ID) and (b.roof.spot >= 0):
            x, y = b.Nav.Pos(b.roof.spot)
        return hyp((x - z.NextCenter[0]), (y - z.NextCenter[1])) < (z.NextRadius - 8)

    def chooseRoof(b):
        # chooseRoof picks the best roof to hide on, with the access point to climb at.
        roofs, _ = b.Nav.Roofs()
        w = b.roof.want
        if (w >= 0) and (w < go_len(roofs)):
            acc, _, ok = b.roofAccessFor(roofs[w], min(b.maxClimb(), b.P.RoofMaxClimb))
            return w, copy(acc), ok
        comp = b.Nav.Components()
        myComp = go_intcast(0, 32)
        c = b.Nav.Nearest(b.pos[0], b.pos[1], 2.9, 9, 6)
        if c >= 0:
            myComp = comp[c]
        limit = min(b.maxClimb(), b.P.RoofMaxClimb)
        bestID, bestS = (-1), 1e18
        bestAcc = world.RoofAccess()
        for i in range(len(roofs)):
            r = roofs[i]
            until, ok_2 = b.roof.ban.get(i, 0.0), i in b.roof.ban
            if ok_2 and (b.t < until):
                continue
            if ((r.Height < b.P.RoofMinHeight) or (r.InnerD < (6 + b.radius))) or (not b.roofSpotOK(r)):
                continue
            if hyp((r.CX - b.pos[0]), (r.CY - b.pos[1])) > (260 + math.sqrt(r.Area)):
                continue
            acc_2 = world.RoofAccess()
            ad = 1e18
            for a in r.Access:
                if (a.Climb > limit) or (a.Climb < 6):
                    continue
                if (myComp != 0) and (comp[a.Ground] != myComp):
                    continue
                if not b.Nav.Walkable(a.Ground, (b.radius + 0.2), b.height):
                    continue
                gx, gy = b.Nav.Pos(a.Ground)
                d = hyp((gx - b.pos[0]), (gy - b.pos[1]))
                if d < ad:
                    acc_2, ad = copy(a), d
            if ad > 1e17:
                continue
            s = ((ad * 1.2) - (min(r.InnerD, 25) * 2.5)) - (min(r.Height, 30) * 1.5)
            ix, iy = b.Nav.Pos(r.Inner)
            if b.P.RoofCenterW > 0:
                z = b.o.Zone
                s += hyp((ix - z.NextCenter[0]), (iy - z.NextCenter[1])) * b.P.RoofCenterW
            _tmp_149 = b.tracks
            for _ in list(_tmp_149):
                if _ not in _tmp_149:
                    continue
                tr = _tmp_149[_]
                if tr.NPC or ((b.t - tr.LastSeen) > 20):
                    continue
                d_2 = hyp((tr.Pos[0] - ix), (tr.Pos[1] - iy))
                if d_2 < 120:
                    s += ((120 - d_2)) * 0.6
            if (i == b.roof.id_) and (b.roof.state != roofNone):
                s -= 40
            if s < bestS:
                bestID, bestS, bestAcc = i, s, copy(acc_2)
        return bestID, copy(bestAcc), (bestID >= 0)

    def roofSpot(b, id_):
        # roofSpot returns where to stand on roof id: climb the distance-to-edge field from where we are.
        roofs, roofOf = b.Nav.Roofs()
        dist = b.Nav.RoofDist()
        r = roofs[id_]
        s = b.roof.spot
        if ((b.roof.want == id_) and (s >= 0)) and (int(roofOf[s]) == id_):
            return b.Nav.Pos(s)
        k = b.Nav.Index(b.pos[0], b.pos[1])
        if int(roofOf[k]) != id_:
            return b.Nav.Pos(r.Inner)
        ix, iy = b.Nav.Pos(r.Inner)
        d = hyp((ix - b.pos[0]), (iy - b.pos[1]))
        steps = int((d / 2)) + 1
        clear = True
        s_2 = 1
        while s_2 <= steps:
            t = go_div(float(s_2), float(steps))
            c = b.Nav.Index((b.pos[0] + (((ix - b.pos[0])) * t)), (b.pos[1] + (((iy - b.pos[1])) * t)))
            if (int(roofOf[c]) != id_) or (dist[c] < 2):
                clear = False
                break
            s_2 += 1
        if clear:
            return ix, iy
        ci, cj = go_remainder(k, b.Nav.NX), go_intdiv(k, b.Nav.NX)
        best, bd = k, dist[k]
        dj = -3
        while dj <= 3:
            di = -3
            while di <= 3:
                i, j = (ci + di), (cj + dj)
                if (((i < 0) or (j < 0)) or (i >= b.Nav.NX)) or (j >= b.Nav.NY):
                    di += 1
                    continue
                c_2 = (j * b.Nav.NX) + i
                if (int(roofOf[c_2]) == id_) and (dist[c_2] > bd):
                    best, bd = c_2, dist[c_2]
                di += 1
            dj += 1
        return b.Nav.Pos(best)

    def roofCover(b, id_, ths):
        # roofCover finds a spot on our roof that none of the given threats can see (body or head), nearest
        # first. It returns -1 when the roof cannot hide us from them.
        roofs, roofOf = b.Nav.Roofs()
        dist = b.Nav.RoofDist()
        r = roofs[id_]
        pass
        eyes = []
        for i in range(len(ths)):
            tr = ths[i].tr
            if (ths[i].d > 280) or ((((b.t - tr.LastSeen) > 8) and (not ths[i].phantom))):
                continue
            sc = tr.scale(b.sizePerCube)
            eyes.append(eyeT_roofCover(tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))))
        if go_len(eyes) == 0:
            return -1
        best, bs = (-1), 1e18
        for c in r.Cells:
            k = int(c)
            ci, cj = go_remainder(k, b.Nav.NX), go_intdiv(k, b.Nav.NX)
            if ((go_remainder(((ci + cj)), 2) != 0) or (dist[k] < 3)) or (int(roofOf[k]) != id_):
                continue
            x, y = b.Nav.Pos(k)
            d = hyp((x - b.pos[0]), (y - b.pos[1]))
            if (d > 50) or (d >= bs):
                continue
            hidden = True
            for e in eyes:
                if b.W.Visible(e.x, e.y, e.z, x, y, (r.Z + (b.height * 0.5))) or b.W.Visible(
                    e.x, e.y, e.z, x, y, (r.Z + (b.height * 0.97))
                ):
                    hidden = False
                    break
            if hidden:
                best, bs = k, d
        return best

    def enemyOnRoof(b, ths):
        # enemyOnRoof reports whether a mech is up here with us (same level, close).
        for i in range(len(ths)):
            tr = ths[i].tr
            if (tr.Listed and (ths[i].d < 70)) and (abs((tr.Pos[2] - b.pos[2])) < 5):
                return True
        return False

    def roofClimbStep(b, act):
        # roofClimb drives the jet climb. It writes the action directly (the ground planner does not apply).
        roofs, roofOf = b.Nav.Roofs()
        r = roofs[b.roof.id_]
        ex, ey = b.Nav.Pos(b.roof.acc.Edge)
        dx, dy = norm2((ex - b.pos[0]), (ey - b.pos[1]))
        act.Move = [dx, dy]
        feet = b.pos[2]
        cell = b.Nav.Index(b.pos[0], b.pos[1])
        over = int(roofOf[cell]) == b.roof.id_
        grounded = b.o.Self.Grounded
        if (grounded and over) and (abs((feet - r.Z)) < 1.6):
            b.roof.state = roofOn
            b.roof.t0 = b.t
            b.roof.tries = 0
            return
        elif grounded and (feet < (r.Z - 1.0)):
            act.Jump = True
        elif feet < (r.Z + 0.7):
            act.Boost = True
        elif not over:
            act.Boost = b.vel[2] < 0.5
        budget = (b.roof.acc.Climb / 8.0) + 5
        if ((b.t - b.roof.t0) > budget) or ((((b.energy < 2) and (not grounded)) and (feet < (r.Z - 0.5)))):
            b.roof.tries += 1
            if b.roof.ban is None:
                b.roof.ban = {}
            b.roof.ban[b.roof.id_] = b.t + 90
            b.roof.state = roofNone

    def overland(b, act, gx, gy):
        # overland travels to a goal over the top surface of the map: walking, dropping off edges and
        # jetting up walls, along a route from Nav.SurfacePath. It is how we move wherever the walk grid
        # does not apply (leaving a roof, out of a walled courtyard, into a circle that closes inside the
        # stadium or on top of a building). It writes the action directly.
        tops = b.Nav.Tops()
        feet = b.pos[2]
        grounded = b.o.Self.Grounded
        here = b.Nav.Index(b.pos[0], b.pos[1])
        if b.surfBan is None:
            b.surfBan = {}
        if (b.t - b.surfWatchT) >= 1.5:
            if (b.surfPushing and (dist3(b.pos, b.surfWatchPos) < 1.2)) and (go_len(b.surf) >= 2):
                j = b.surfIdx + 1
                while (j < go_len(b.surf)) and (j <= (b.surfIdx + 3)):
                    b.surfBan[int(b.surf[j])] = b.t + 25
                    j += 1
                b.surf = []
                b.surfT = -100
            b.surfWatchT, b.surfWatchPos, b.surfPushing = b.t, (b.pos).copy(), False
        replan = ((go_len(b.surf) < 2) or (hyp((gx - b.surfGoal[0]), (gy - b.surfGoal[1])) > 6)) or (
            (b.t - b.surfT) > 1.2
        )
        if not replan:
            px, py = b.Nav.Pos(int(b.surf[b.surfIdx]))
            if hyp((px - b.pos[0]), (py - b.pos[1])) > 7:
                replan = True
        if replan and ((b.t - b.surfT) >= 0.3):

            def _tmp_160(k):
                until, ok = b.surfBan.get(k, 0.0), k in b.surfBan
                return ok and (b.t < until)

            blocked = _tmp_160
            b.surf = b.Nav.SurfacePath(
                b.pos[0], b.pos[1], feet, gx, gy, b.maxClimb(), b.radius, 14000, blocked
            )
            b.surfGoal = [gx, gy]
            b.surfT = b.t
            b.surfIdx = 0
        dx, dy = norm2((gx - b.pos[0]), (gy - b.pos[1]))
        need = feet
        if go_len(b.surf) >= 2:
            best, bd = b.surfIdx, 1e18
            j_2 = b.surfIdx
            while (j_2 < go_len(b.surf)) and (j_2 < (b.surfIdx + 8)):
                px_2, py_2 = b.Nav.Pos(int(b.surf[j_2]))
                d = hyp((px_2 - b.pos[0]), (py_2 - b.pos[1]))
                if d < bd:
                    best, bd = j_2, d
                j_2 += 1
            b.surfIdx = best
            n1 = best + 1
            if n1 > (go_len(b.surf) - 1):
                n1 = go_len(b.surf) - 1
            tgt = n1
            while (
                ((tgt < (go_len(b.surf) - 1)) and (tgt < (best + 3)))
                and (abs((float(tops[b.surf[(tgt + 1)]]) - float(tops[b.surf[n1]]))) < 0.6)
            ) and (float(tops[b.surf[n1]]) <= (feet + 1.0)):
                tgt += 1
            tx, ty = b.Nav.Pos(int(b.surf[tgt]))
            if int(b.surf[tgt]) != here:
                dx, dy = norm2((tx - b.pos[0]), (ty - b.pos[1]))
            need = float(tops[b.surf[n1]])
            h = float(tops[b.surf[tgt]])
            if h > need:
                need = h
        else:
            for s in [(b.radius + 1), (b.radius + 3.5)]:
                h_2, _ = b.W.Floor((b.pos[0] + (dx * s)), (b.pos[1] + (dy * s)), 1e9)
                if h_2 > need:
                    need = h_2
        act.Move = [dx, dy]
        rise = need - feet
        drain = stat(b.o.Self.Stats, "jet_drain", b.mech("jet_drain", 15))
        if rise < 1.0:
            act.Boost = (grounded and (not b.o.Self.InZone)) and (b.energy > 70)
            b.surfPushing = True
        elif grounded:
            if b.energy >= min((((rise / 8.9) * drain) + 16), (b.o.Self.MaxEnergy - 3)):
                act.Jump = True
                b.surfPushing = True
            else:
                act.Move = [0, 0]
        else:
            act.Boost = (feet < (need + 0.8)) and (b.energy > 1)

    def mainComp(b):
        # mainComp returns the id of the largest walkable region (the open map).
        if b.mainCompID != 0:
            return b.mainCompID
        comp = b.Nav.Components()
        counts = {}
        for c in comp:
            if c != 0:
                counts[c] = counts.get(c, 0) + 1
        best, bn = go_intcast(0, 32), 0
        _tmp_166 = counts
        for c_2 in list(_tmp_166):
            if c_2 not in _tmp_166:
                continue
            n = _tmp_166[c_2]
            if n > bn:
                best, bn = c_2, n
        b.mainCompID = best
        return best

    def roofWanted(b, st, zi):
        # roofWanted reports whether hiding on a roof is what we want right now.
        if ((not b.P.UseRoofs) or zi.final) or (b.o.Zone.NextRadius < b.P.RoofMinZone):
            return False
        if st.name == "duel":
            return False
        if (not st.stealth) and (not b.P.RoofInSquad):
            if not (((b.P.BrawlRoofs and st.avoid) and (st.name == "ffa"))):
                return False
            if ((b.has("laser") < 0) and (b.o.Self.Cubes < b.P.BrawlRoofCubes)) and (
                b.t < b.P.BrawlRoofAfter
            ):
                return False
        return True

    def roofPlanStep(b, wanted, act):
        # roofPlanStep runs the roof plan when roofs are wanted; ok=false means "use the ground hide instead".
        gx = 0.0
        gy = 0.0
        settled = False
        ok = False
        if not wanted:
            b.roof.state = roofNone
            return 0, 0, False, False
        return b.roofHold(act)

    def hideoutFor(b, st, zi, allowRoof):
        # hideoutFor is the policy's entry to the hideout chooser: stealth stances only, and it leaves the
        # roof plan pointed at the chosen roof (or free to choose by the older rule when the map is not used).
        if (b.hm is None) or (not ((st.stealth or ((b.P.HoldHideMap and st.avoid))))):
            b.roof.want, b.roof.spot = (-1), (-1)
            return hideout(), False
        if not st.stealth:
            allowRoof = False
        ho, ok = b.hideoutStep(zi, allowRoof)
        if not ok:
            b.roof.want, b.roof.spot = (-1), (-1)
            return copy(ho), False
        if ho.class_ == hmRoof:
            b.roof.want, b.roof.spot = ho.roof, ho.cell
        return copy(ho), True

    def hideoutStep(b, zi, allowRoof):
        # hideoutStep returns the hideout to use right now (re-evaluated every couple of seconds, at once
        # when the current one falls outside the circle we must end up in).
        if b.hm is None:
            return hideout(), False
        stale = ((b.t - b.hideOutT) > 2.0) or (not b.hideOutOK)
        if b.hideOutOK and (not stale):
            z = b.o.Zone
            x, y = b.Nav.Pos(b.hideOut.cell)
            if (hyp((x - z.NextCenter[0]), (y - z.NextCenter[1])) > (z.NextRadius - 4)) or (
                ((b.hideOut.class_ == hmRoof) and (not allowRoof))
            ):
                stale = True
        if stale:
            b.hideOut, b.hideOutOK = b.chooseHideout(zi, allowRoof)
            b.hideOutT = b.t
            if b.hideOutOK:
                b.hideCell = b.hideOut.cell
            else:
                b.hideCell = -1
        return copy(b.hideOut), b.hideOutOK

    def roofHold(b, act):
        # roofHold is the "nothing else to do" behaviour when roofs are in play. It returns the goal to walk
        # to and whether we are settled (stand still). ok=false means no roof plan: fall back to ground hiding.
        gx = 0.0
        gy = 0.0
        settled = False
        ok = False
        roofs, _ = b.Nav.Roofs()
        if (b.t - b.roof.stepT) > 1.5:
            b.roof.t0 = b.t
        b.roof.stepT = b.t
        id_ = b.onRoof()
        if (id_ >= 0) and b.o.Self.Grounded:
            r = roofs[id_]
            stay = b.roofSpotOK(r) and (r.Height >= (b.P.RoofMinHeight - 3))
            if b.roof.want >= 0:
                stay = (id_ == b.roof.want) and b.roofSpotOK(r)
            if stay and b.P.RoofStandCheck:
                z = b.o.Zone
                sx, sy = b.roofSpot(id_)
                if hyp((sx - z.NextCenter[0]), (sy - z.NextCenter[1])) > (z.NextRadius - 4):
                    stay = False
                    if b.roof.ban is None:
                        b.roof.ban = {}
                    b.roof.ban[id_] = b.t + 60
            if (not stay) and b.holdRoofMove:
                stay = True
            if stay:
                b.roof.state, b.roof.id_ = roofOn, id_
                x, y = b.roofSpot(id_)
                return x, y, (hyp((x - b.pos[0]), (y - b.pos[1])) < 2.0), True
            b.roof.state = roofNone
        if b.roof.state == roofOn:
            b.roof.state = roofNone
        if (b.roof.state == roofNone) or ((b.t - b.roof.chosen) > 3):
            id__2, acc, found = b.chooseRoof()
            b.roof.chosen = b.t
            if not found:
                b.roof.state = roofNone
                return 0, 0, False, False
            if (b.roof.state == roofNone) or (id__2 != b.roof.id_):
                b.roof.state, b.roof.id_, b.roof.acc, b.roof.t0 = roofApproach, id__2, copy(acc), b.t
        gx, gy = b.Nav.Pos(b.roof.acc.Ground)
        d = hyp((gx - b.pos[0]), (gy - b.pos[1]))
        if (d < 1.6) and b.onGroundLevel():
            need = ((b.roof.acc.Climb / 8.9) * stat(b.o.Self.Stats, "jet_drain", 15)) + 24
            if b.holdClimb:
                if b.roof.waitT0 <= 0:
                    b.roof.waitT0 = b.t
                if (b.t - b.roof.waitT0) > 4:
                    if b.roof.ban is None:
                        b.roof.ban = {}
                    b.roof.ban[b.roof.id_] = b.t + 20
                    b.roof.state = roofNone
                    b.roof.waitT0 = 0
                    return 0, 0, False, False
                return gx, gy, True, True
            b.roof.waitT0 = 0
            if b.energy >= need:
                b.roof.state = roofClimb
                b.roof.t0 = b.t
            return gx, gy, True, True
        if (b.t - b.roof.t0) > 60:
            if b.roof.ban is None:
                b.roof.ban = {}
            b.roof.ban[b.roof.id_] = b.t + 60
            b.roof.state = roofNone
            return 0, 0, False, False
        return gx, gy, False, True

    def zoneInfo(b):
        z = b.o.Zone
        zi = zoneInfo()
        dn = hyp((b.pos[0] - z.NextCenter[0]), (b.pos[1] - z.NextCenter[1]))
        dc = hyp((b.pos[0] - z.Center[0]), (b.pos[1] - z.Center[1]))
        zi.outNext = dn - z.NextRadius
        zi.outCur = dc - z.Radius
        zi.tPass = go_inf(1)
        zi.final = z.NextRadius < 12
        t0 = max(b.t, z.ShrinkStart)
        if zi.outCur > 0:
            zi.tPass = 0
        elif (zi.outNext > 0) and (z.ShrinkEnd > t0):
            i = 1
            while i <= 50:
                f = float(i) / 50
                cx = z.Center[0] + (((z.NextCenter[0] - z.Center[0])) * f)
                cy = z.Center[1] + (((z.NextCenter[1] - z.Center[1])) * f)
                r = z.Radius + (((z.NextRadius - z.Radius)) * f)
                if hyp((b.pos[0] - cx), (b.pos[1] - cy)) > r:
                    zi.tPass = ((t0 - b.t)) + (f * ((z.ShrinkEnd - t0)))
                    break
                i += 1
        elif (zi.outNext > 0) and (z.ShrinkEnd <= t0):
            zi.tPass = 0
        dx, dy = norm2((b.pos[0] - z.NextCenter[0]), (b.pos[1] - z.NextCenter[1]))
        gr = min((z.NextRadius * 0.6), (z.NextRadius - 10))
        if gr < 0:
            gr = 0
        zi.goal = [(z.NextCenter[0] + (dx * gr)), (z.NextCenter[1] + (dy * gr))]
        zi.walkable = True
        key = [z.NextCenter[0], z.NextCenter[1], z.NextRadius]
        if ((key != b.zgKey) or ((b.t - b.zgT) > 1.0)) or (b.zgComp != b.myComp):
            b.zgKey, b.zgT, b.zgComp = (key).copy(), b.t, b.myComp
            margin = min(5, (z.NextRadius * 0.3))
            base = math.atan2(dy, dx)
            found, foundAny = False, False
            anyGoal = [0.0] * 2
            for fr in [0.6, 0.45, 0.75, 0.3, 0.15, 0.9, 0.0]:
                try:
                    rr = max(0, min((z.NextRadius * fr), (z.NextRadius - 10)))
                    for off in [0, 0.4, (-0.4), 0.8, (-0.8), 1.4, (-1.4), 2.2, (-2.2), math.pi]:
                        x, y = (z.NextCenter[0] + (math.cos((base + off)) * rr)), (
                            z.NextCenter[1] + (math.sin((base + off)) * rr)
                        )
                        k = b.Nav.Nearest(x, y, (b.radius + 0.3), b.height, 4)
                        if k < 0:
                            continue
                        px, py = b.Nav.Pos(k)
                        if (z.NextRadius > 12) and (
                            hyp((px - z.NextCenter[0]), (py - z.NextCenter[1])) > (z.NextRadius - margin)
                        ):
                            continue
                        if not b.sameComp(k):
                            if not foundAny:
                                foundAny, anyGoal = True, [px, py]
                            continue
                        b.zgGoal, found = [px, py], True
                        raise StopIteration("_tmp_169break")
                except StopIteration as _go_flow:
                    if _go_flow.args == ("_tmp_169break",):
                        break
                    if _go_flow.args != ("_tmp_169continue",):
                        raise
            b.zgWalk = found
            if not found:
                if foundAny:
                    b.zgGoal = (anyGoal).copy()
                else:
                    b.zgGoal = [z.NextCenter[0], z.NextCenter[1]]
        zi.goal, zi.walkable = (b.zgGoal).copy(), b.zgWalk
        need = 0.0
        if zi.outNext > 0:
            need = (go_div(((zi.outNext + 8)), b.walk) * 1.35) + 4
            if (not zi.walkable) and (b.P.OverlandEarly > 0):
                need = (need * b.P.OverlandEarly) + 25
        zi.critical = (zi.outCur > (-2)) or (zi.tPass < 2.5)
        zi.urgent = (
            (zi.critical or (zi.tPass < 9)) or (((zi.outNext > 0) and ((z.ShrinkEnd - b.t) < need)))
        ) or (((zi.outNext > 0) and ((zi.tPass - need) < 3)))
        return copy(zi)

    def assess(b):
        out = []
        _tmp_171 = b.tracks
        for _ in list(_tmp_171):
            if _ not in _tmp_171:
                continue
            tr = _tmp_171[_]
            if tr.NPC:
                continue
            phantom = ((not tr.Listed) and ((b.t - tr.PhantomT) < 4)) and ((b.t - tr.LastSeen) > 1)
            if ((b.t - tr.LastSeen) > 8) and (not phantom):
                continue
            d = dist3(b.pos, tr.Pos)
            th = threat(tr=tr, d=d, phantom=phantom)
            th.adv, th.rmin, th.rmax = b.fightPlan(tr, d)
            if ((b.P.ExchangeW > 0) and (not tr.NPC)) and (((tr.HurtMe > 1) or (tr.IHurt > 1))):
                ex = go_div(((tr.IHurt + 150)), ((tr.HurtMe + 150)))
                th.adv *= math.pow(clamp(ex, 0.4, 1.8), b.P.ExchangeW)
            th.dps = b.theirDPS(tr, d)
            aimR = 200.0
            if (tr.Laser and (b.P.LaserAimRange > aimR)) and b.realModel():
                aimR = b.P.LaserAimRange
            th.engaged = (
                ((b.t - tr.HurtMeT) < 4) or (((tr.LOS and ((b.t - tr.AimAtMeT) < 0.6)) and (d < aimR)))
            ) or ((tr.LOS and (d < 40)))
            if ((not th.engaged) and tr.LOS) and (d < 90):
                bear = math.atan2((b.pos[1] - tr.Pos[1]), (b.pos[0] - tr.Pos[0]))
                closing = go_div(
                    (((tr.Vel[0] * ((b.pos[0] - tr.Pos[0]))) + (tr.Vel[1] * ((b.pos[1] - tr.Pos[1]))))),
                    max(d, 1),
                )
                if (abs(angDiff(tr.Aim[0], bear)) < 0.5) and (closing > 4):
                    th.engaged = True
            if phantom:
                th.engaged = True
                th.dps = max(th.dps, (tr.HurtMe / 3))
                th.adv = min(th.adv, 0.5)
            if th.engaged:
                tr.EngT = b.t
            elif ((b.t - tr.EngT) < 0.8) and tr.Listed:
                th.engaged = True
            out.append(copy(th))
        return out

    def sameComp(b, cell):
        # sameComp reports whether a nav cell is in the walkable region we are standing in.
        if (b.myComp == 0) or (cell < 0):
            return True
        c = b.Nav.Components()[cell]
        return c == b.myComp

    def reachable(b, x, y):
        # reachable reports whether a ground point can be walked to from here (same walkable region).
        if b.myComp == 0:
            return True
        c = b.Nav.Nearest(x, y, 2.9, 9, 3)
        return (c >= 0) and (b.Nav.Components()[c] == b.myComp)

    def hiddenHere(b, ths):
        # hiddenHere reports whether none of the threats can see us where we stand right now.
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((((b.t - tr.LastSeen) > 6) and (not ths[i].phantom))) or (ths[i].d > 260):
                continue
            sc = tr.scale(b.sizePerCube)
            ex, ey, ez = tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))
            if b.W.Visible(ex, ey, ez, b.pos[0], b.pos[1], (b.pos[2] + (b.height * 0.5))) or b.W.Visible(
                ex, ey, ez, b.pos[0], b.pos[1], (b.pos[2] + (b.height * 0.95))
            ):
                return False
        return True

    def findCover(b, ths, maxCost):
        # findCover looks for the nearest walkable cell hidden from every listed threat.
        pass
        eyes = []
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((((b.t - tr.LastSeen) > 6) and (not ths[i].phantom))) or (ths[i].d > 260):
                continue
            sc = tr.scale(b.sizePerCube)
            eyes.append(eyeT_findCover(tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))))
        if go_len(eyes) == 0:
            return -1
        z = b.o.Zone
        found = -1
        checked = 0

        def _tmp_175(k, cost):
            nonlocal checked
            nonlocal found
            if go_remainder(((go_remainder(k, b.Nav.NX) + go_intdiv(k, b.Nav.NX))), 2) != 0:
                return True
            if float(b.Nav.Clear[k]) < (b.radius + 0.6):
                return True
            x, y = b.Nav.Pos(k)
            if hyp((x - z.Center[0]), (y - z.Center[1])) > (z.Radius - 6):
                return True
            if ((z.ShrinkEnd - b.t) < 25) and (
                hyp((x - z.NextCenter[0]), (y - z.NextCenter[1])) > (z.NextRadius - 4)
            ):
                return True
            checked += 1
            if checked > 700:
                return False
            gz = float(b.Nav.Z[k])
            for e in eyes:
                if b.W.Visible(e.x, e.y, e.z, x, y, (gz + (b.height * 0.5))) or b.W.Visible(
                    e.x, e.y, e.z, x, y, (gz + (b.height * 0.95))
                ):
                    return True
            found = k
            return False

        b.Nav.Flood(b.pos[0], b.pos[1], (b.radius + 0.15), b.height, maxCost, None, _tmp_175)
        return found

    def cellHidden(b, k, ths):
        # cellHidden reports whether a mech standing in the cell is out of sight of every recent threat's
        # last known position.
        x, y = b.Nav.Pos(k)
        gz = float(b.Nav.Z[k])
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((((b.t - tr.LastSeen) > 6) and (not ths[i].phantom))) or (ths[i].d > 260):
                continue
            sc = tr.scale(b.sizePerCube)
            ex, ey, ez = tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))
            if b.W.Visible(ex, ey, ez, x, y, (gz + (b.height * 0.5))) or b.W.Visible(
                ex, ey, ez, x, y, (gz + (b.height * 0.95))
            ):
                return False
        return True

    def nearestEye(b, ths):
        # nearestEye is the distance to the nearest recent threat's last known position (1e9: none).
        d0 = 1e9
        for i in range(len(ths)):
            tr = ths[i].tr
            if ((((b.t - tr.LastSeen) > 6) and (not ths[i].phantom))) or (ths[i].d > 260):
                continue
            d = hyp((tr.Pos[0] - b.pos[0]), (tr.Pos[1] - b.pos[1]))
            if d < d0:
                d0 = d
        return d0

    def weaponValue(b, kind):
        # weaponValue ranks the weapons for pickup and swap decisions.
        _tmp_179 = kind
        if _tmp_179 == "laser":
            return b.P.LaserValue
        elif _tmp_179 == "lightning":
            return b.P.LightningValue
        elif _tmp_179 == "mortar":
            return 1.2
        elif _tmp_179 == "gun":
            return 2.0
        return 0

    def wantPickup(b, kind):
        # wantPickup reports whether we would take this weapon and which slot it would replace (-1: empty slot).
        if b.has(kind) >= 0:
            return False, (-1)
        cookoff = stat(b.C.Weapons.get("laser", {}), "cookoff", 0)
        if ((kind == "mortar") and b.P.NoMortar) and (
            (b.realModel() or ((b.P.AllNoMortar and (cookoff > 0))))
        ):
            return False, (-1)
        i = 0
        while i < 2:
            if not b.slots[i].ok:
                return True, (-1)
            i += 1
        worst, wv = (-1), 1e9
        i_2 = 0
        while i_2 < 2:
            if b.slots[i_2].kind == "gun":
                i_2 += 1
                continue
            v = b.weaponValue(b.slots[i_2].kind)
            if v < wv:
                worst, wv = i_2, v
            i_2 += 1
        if ((worst >= 0) and (b.weaponValue(kind) > (wv + 0.3))) and (b.slots[worst].charge <= 0):
            return True, worst
        return False, (-1)

    def inFutureZone(b, x, y, secs, margin):
        # inFutureZone reports whether a point will still be inside the zone in `secs` seconds (roughly).
        z = b.o.Zone
        if hyp((x - z.Center[0]), (y - z.Center[1])) > (z.Radius - margin):
            return False
        if (b.t + secs) > z.ShrinkStart:
            f = 1.0
            if z.ShrinkEnd > z.ShrinkStart:
                f = clamp(go_div((((b.t + secs) - z.ShrinkStart)), ((z.ShrinkEnd - z.ShrinkStart))), 0, 1)
            cx = z.Center[0] + (((z.NextCenter[0] - z.Center[0])) * f)
            cy = z.Center[1] + (((z.NextCenter[1] - z.Center[1])) * f)
            r = z.Radius + (((z.NextRadius - z.Radius)) * f)
            if hyp((x - cx), (y - cy)) > (r - margin):
                return False
        return True

    def enemyNear(b, pos, r):
        _tmp_183 = b.tracks
        for _ in list(_tmp_183):
            if _ not in _tmp_183:
                continue
            tr = _tmp_183[_]
            if tr.NPC or ((b.t - tr.LastSeen) > 6):
                continue
            if dist2(tr.Pos, pos) < r:
                return True
        return False

    def chooseLoot(b, danger, st):
        best = None
        watchEyes = []
        strict = b.shyPhase(st)
        mem = 4.0
        if strict:
            mem = b.P.ShyMem
        if (((b.P.LootHiddenBias > 0) or strict)) and st.avoid:
            _tmp_185 = b.tracks
            for _ in list(_tmp_185):
                if _ not in _tmp_185:
                    continue
                tr = _tmp_185[_]
                if tr.NPC or ((b.t - tr.LastSeen) > mem):
                    continue
                sc = tr.scale(b.sizePerCube)
                watchEyes.append([tr.Pos[0], tr.Pos[1], (tr.Pos[2] + (8 * sc))])
                if go_len(watchEyes) >= 6:
                    break

        def _tmp_187(l, value, handling):
            nonlocal best
            d = dist2(b.pos, l.pos)
            if d > st.lootRadius:
                return
            until, banned = b.banUntil.get(l.id_, 0.0), l.id_ in b.banUntil
            if banned and (b.t < until):
                return
            if not b.reachable(l.pos[0], l.pos[1]):
                return
            if st.stealth:
                e = b.Nav.Exposure().At(b.Nav.Index(l.pos[0], l.pos[1]))
                if e <= 1:
                    value *= 1 - (0.6 * float(e))
            tt = go_div((d * 1.25), b.walk) + handling
            if not b.inFutureZone(l.pos[0], l.pos[1], ((tt + 2) + b.P.ZoneSlack), 6):
                return
            if b.enemyNear(l.pos, 45) and (l.kind != "cube"):
                value *= 0.35
            isLaser = False
            if (l.kind == "pickup") and (b.has("laser") < 0):
                it = b.pickups.get(l.id_, None)
                if (it is not None) and (it.Kind == "laser"):
                    isLaser = True
            if strict:
                if ((b.P.ShyLootRadius > 0) and (d > b.P.ShyLootRadius)) and (not isLaser):
                    return
                if b.P.ShyExposure > 0:
                    e_2 = b.Nav.Exposure().At(b.Nav.Index(l.pos[0], l.pos[1]))
                    if e_2 <= 1:
                        value *= 1 - (b.P.ShyExposure * float(e_2))
            if strict and (go_len(watchEyes) > 0):
                laserHere = isLaser and (d < b.P.ShyLaser)
                if not laserHere:
                    for e_3 in watchEyes:
                        de = hyp((e_3[0] - l.pos[0]), (e_3[1] - l.pos[1]))
                        if (de < 230) and b.W.Visible(
                            e_3[0], e_3[1], e_3[2], l.pos[0], l.pos[1], (l.pos[2] + 4.5)
                        ):
                            return
                        if (de < 150) and (de < (hyp((e_3[0] - b.pos[0]), (e_3[1] - b.pos[1])) - 10)):
                            return
            elif ((b.P.LootHiddenBias > 0) and st.avoid) and (go_len(watchEyes) > 0):
                for e_4 in watchEyes:
                    if (hyp((e_4[0] - l.pos[0]), (e_4[1] - l.pos[1])) < 230) and b.W.Visible(
                        e_4[0], e_4[1], e_4[2], l.pos[0], l.pos[1], (l.pos[2] + 4.5)
                    ):
                        value *= 1 - b.P.LootHiddenBias
                        break
            l.score = go_div(value, ((tt + 1.5)))
            if l.id_ == b.lootID:
                l.score *= 1.25
            if (best is None) or (l.score > best.score):
                c = copy(l)
                best = c

        consider = _tmp_187
        wantCubes = b.o.Self.Cubes < st.wantCubes
        _tmp_190 = b.pickups
        for _ in list(_tmp_190):
            if _ not in _tmp_190:
                continue
            it_2 = _tmp_190[_]
            if not it_2.Ground:
                continue
            ok, rep = b.wantPickup(it_2.Kind)
            if ok:
                v = b.weaponValue(it_2.Kind) * 4
                if rep >= 0:
                    v = ((b.weaponValue(it_2.Kind) - b.weaponValue(b.slots[rep].kind))) * 4
                consider(loot(kind="pickup", id_=it_2.ID, pos=it_2.Pos), v, 0.5)
        if wantCubes:
            _tmp_192 = b.cubes
            for _ in list(_tmp_192):
                if _ not in _tmp_192:
                    continue
                it_3 = _tmp_192[_]
                if it_3.Ground:
                    consider(loot(kind="cube", id_=it_3.ID, pos=it_3.Pos), 11, 0)
            _tmp_194 = b.crates
            for _ in list(_tmp_194):
                if _ not in _tmp_194:
                    continue
                it_4 = _tmp_194[_]
                if it_4.Ground:
                    consider(loot(kind="crate", id_=it_4.ID, pos=it_4.Pos, shoot=True), 7, 2.5)
            if not danger:
                _tmp_196 = b.tracks
                for _ in list(_tmp_196):
                    if _ not in _tmp_196:
                        continue
                    tr_2 = _tmp_196[_]
                    if tr_2.NPC and ((b.t - tr_2.LastSeen) < 20):
                        k = b.Nav.Index(tr_2.Pos[0], tr_2.Pos[1])
                        if (not b.Nav.Solid[k]) and (abs((float(b.Nav.Z[k]) - tr_2.Pos[2])) < 4):
                            consider(loot(kind="npc", id_=tr_2.ID, pos=tr_2.Pos, shoot=True), 11, 5)
        for i in range(len(b.o.Drops)):
            dr = b.o.Drops[i]
            d_2 = dist2(b.pos, dr.Pos)
            if d_2 > b.P.DropRadius:
                continue
            if (dr.LandsIn > ((go_div(d_2, b.walk) * 1.3) + 6)) and (
                not ((b.P.DropStick and (dr.ID == b.lootID)))
            ):
                continue
            if ((b.P.DropStick and st.avoid) and (b.o.Self.Cubes >= st.wantCubes)) and (
                b.hp > (b.maxHP * 0.7)
            ):
                continue
            if ((dr.Holder is not None) and (dr.Holder != b.o.Self.ID)) and st.stealth:
                continue
            if st.stealth and b.enemyNear(dr.Pos, 110):
                continue
            v_2 = (30.0 * b.P.DropGreed) * 2
            if b.hp < (b.maxHP * 0.6):
                v_2 *= 1.5
            saved = st.lootRadius
            st.lootRadius = b.P.DropRadius
            consider(loot(kind="drop", id_=dr.ID, pos=dr.Pos), v_2, (4 + (dr.LandsIn * 0.3)))
            st.lootRadius = saved
        return best

    def pickUpgrade(b, act):
        of = b.o.Offer
        if (of is None) or (go_len(of.Choices) == 0):
            return
        best, bv = 0, (-1.0)
        for i, c in enumerate(of.Choices):
            v, ok = upgradeRank.get(c.ID, 0.0), c.ID in upgradeRank
            if not ok:
                v = 0.25
            if (b.has("lightning") >= 0) and (((c.ID == "reactor") or (c.ID == "capacitor"))):
                v += 0.3
            if (c.ID == "nanites") and (b.P.NanoBoost > 0):
                v += b.P.NanoBoost
            if v > bv:
                best, bv = i, v
        act.Pick = best

    def manageWeapons(b, act):
        # manageWeapons takes a wanted weapon when we stand on it.
        if b.t < b.takeT:
            return
        reach = b.C.Loot.PickupRadius
        if reach <= 0:
            reach = 4
        bestID, bestV, bestRep = (-1), 0.0, (-1)
        _tmp_200 = b.pickups
        for _ in list(_tmp_200):
            if _ not in _tmp_200:
                continue
            it = _tmp_200[_]
            if (b.t - it.LastSeen) > 0.5:
                continue
            if (dist2(b.pos, it.Pos) > (reach - 0.3)) or (abs((it.Pos[2] - b.pos[2])) > 3.7):
                continue
            ok, rep = b.wantPickup(it.Kind)
            if ok:
                v = b.weaponValue(it.Kind)
                if v > bestV:
                    bestID, bestV, bestRep = it.ID, v, rep
        if bestID >= 0:
            act.Take = bestID
            if bestRep >= 0:
                act.Drop = bestRep
            b.takeT = b.t + 0.25


class agg_Act:
    __slots__ = ["dmg", "d", "n", "seen", "w"]

    def __init__(self, dmg=0.0, d=0.0, n=0, seen=0, w=""):
        self.dmg = dmg
        self.d = d
        self.n = n
        self.seen = seen
        self.w = w


class shot:
    __slots__ = ["ok", "yaw", "pitch", "tf", "point", "dist", "clear"]

    def __init__(self, ok=False, yaw=0.0, pitch=0.0, tf=0.0, point=_MISSING, dist=0.0, clear=False):
        self.ok = ok
        self.yaw = yaw
        self.pitch = pitch
        self.tf = tf
        self.point = [0.0] * 3 if point is _MISSING else point
        self.dist = dist
        self.clear = clear

    def __copy__(self):
        other = object.__new__(type(self))
        other.ok = self.ok
        other.yaw = self.yaw
        other.pitch = self.pitch
        other.tf = self.tf
        other.point = self.point.copy()
        other.dist = self.dist
        other.clear = self.clear
        return other


class aimTarget:
    __slots__ = [
        "pos",
        "vel",
        "radius",
        "centerZ",
        "mech",
        "lead",
        "leadSet",
        "gunLead",
        "gunLeadSet",
        "rear",
        "hasMortar",
    ]

    def __init__(
        self,
        pos=_MISSING,
        vel=_MISSING,
        radius=0.0,
        centerZ=0.0,
        mech=False,
        lead=0.0,
        leadSet=False,
        gunLead=0.0,
        gunLeadSet=False,
        rear=False,
        hasMortar=False,
    ):
        self.pos = [0.0] * 3 if pos is _MISSING else pos
        self.vel = [0.0] * 3 if vel is _MISSING else vel
        self.radius = radius
        self.centerZ = centerZ
        self.mech = mech
        self.lead = lead
        self.leadSet = leadSet
        self.gunLead = gunLead
        self.gunLeadSet = gunLeadSet
        self.rear = rear
        self.hasMortar = hasMortar

    def __copy__(self):
        other = object.__new__(type(self))
        other.pos = self.pos.copy()
        other.vel = self.vel.copy()
        other.radius = self.radius
        other.centerZ = self.centerZ
        other.mech = self.mech
        other.lead = self.lead
        other.leadSet = self.leadSet
        other.gunLead = self.gunLead
        other.gunLeadSet = self.gunLeadSet
        other.rear = self.rear
        other.hasMortar = self.hasMortar
        return other


class eyeT_deeperCover:
    __slots__ = ["x", "y", "z"]

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class stance:
    __slots__ = ["name", "engageRatio", "disengage", "hunt", "stealth", "avoid", "lootRadius", "wantCubes"]

    def __init__(
        self,
        name="",
        engageRatio=0.0,
        disengage=0.0,
        hunt=False,
        stealth=False,
        avoid=False,
        lootRadius=0.0,
        wantCubes=0,
    ):
        self.name = name
        self.engageRatio = engageRatio
        self.disengage = disengage
        self.hunt = hunt
        self.stealth = stealth
        self.avoid = avoid
        self.lootRadius = lootRadius
        self.wantCubes = wantCubes


class hideCand:
    __slots__ = ["cell", "score"]

    def __init__(self, cell=0, score=0.0):
        self.cell = cell
        self.score = score


class hideMap:
    __slots__ = ["ok", "nx", "ny", "step", "lw", "lh", "class_", "seen", "hit", "cells"]

    def __init__(
        self,
        ok=False,
        nx=0,
        ny=0,
        step=0,
        lw=0,
        lh=0,
        class_=_MISSING,
        seen=_MISSING,
        hit=_MISSING,
        cells=_MISSING,
    ):
        self.ok = ok
        self.nx = nx
        self.ny = ny
        self.step = step
        self.lw = lw
        self.lh = lh
        self.class_ = [] if class_ is _MISSING else class_
        self.seen = [] if seen is _MISSING else seen
        self.hit = [] if hit is _MISSING else hit
        self.cells = [] if cells is _MISSING else cells

    def lat(h, k):
        return ((go_intdiv(go_intdiv(k, h.nx), h.step)) * h.lw) + go_intdiv((go_remainder(k, h.nx)), h.step)

    def at(h, k):
        # at returns the class and the seen-from / hittable-from fractions for the lattice cell holding nav cell k.
        i = h.lat(k)
        if (i < 0) or (i >= go_len(h.class_)):
            return hmNone, 1, 1
        return h.class_[i], float(h.seen[i]), float(h.hit[i])


class hideout:
    __slots__ = ["cell", "class_", "z", "roof", "score"]

    def __init__(self, cell=0, class_=0, z=0.0, roof=0, score=0.0):
        self.cell = cell
        self.class_ = class_
        self.z = z
        self.roof = roof
        self.score = score


class cnd_chooseHideout:
    __slots__ = ["h", "d"]

    def __init__(self, h=_MISSING, d=0.0):
        self.h = hideout() if h is _MISSING else h
        self.d = d

    def __copy__(self):
        other = object.__new__(type(self))
        other.h = copy(self.h)
        other.d = self.d
        return other


class racc_chooseHideout:
    __slots__ = ["done", "ok", "acc", "d"]

    def __init__(self, done=False, ok=False, acc=_MISSING, d=0.0):
        self.done = done
        self.ok = ok
        self.acc = world.RoofAccess() if acc is _MISSING else acc
        self.d = d

    def __copy__(self):
        other = object.__new__(type(self))
        other.done = self.done
        other.ok = self.ok
        other.acc = copy(self.acc)
        other.d = self.d
        return other


class cand:
    __slots__ = ["dx", "dy", "boost", "score"]

    def __init__(self, dx=0.0, dy=0.0, boost=False, score=0.0):
        self.dx = dx
        self.dy = dy
        self.boost = boost
        self.score = score


class incoming:
    __slots__ = ["mortar", "pos", "vel", "maxT", "impact", "dmg", "splash"]

    def __init__(
        self, mortar=False, pos=_MISSING, vel=_MISSING, maxT=0.0, impact=_MISSING, dmg=0.0, splash=0.0
    ):
        self.mortar = mortar
        self.pos = [0.0] * 3 if pos is _MISSING else pos
        self.vel = [0.0] * 3 if vel is _MISSING else vel
        self.maxT = maxT
        self.impact = [0.0] * 3 if impact is _MISSING else impact
        self.dmg = dmg
        self.splash = splash

    def __copy__(self):
        other = object.__new__(type(self))
        other.mortar = self.mortar
        other.pos = self.pos.copy()
        other.vel = self.vel.copy()
        other.maxT = self.maxT
        other.impact = self.impact.copy()
        other.dmg = self.dmg
        other.splash = self.splash
        return other


class steerReq:
    __slots__ = [
        "wantX",
        "wantY",
        "wantW",
        "boost",
        "slow",
        "posCost",
        "hold",
        "threats",
        "lookTicks",
        "dodgeBoost",
        "fenceRoof",
        "zoneFree",
    ]

    def __init__(
        self,
        wantX=0.0,
        wantY=0.0,
        wantW=0.0,
        boost=False,
        slow=False,
        posCost=None,
        hold=False,
        threats=_MISSING,
        lookTicks=0,
        dodgeBoost=False,
        fenceRoof=False,
        zoneFree=False,
    ):
        self.wantX = wantX
        self.wantY = wantY
        self.wantW = wantW
        self.boost = boost
        self.slow = slow
        self.posCost = posCost
        self.hold = hold
        self.threats = [] if threats is _MISSING else threats
        self.lookTicks = lookTicks
        self.dodgeBoost = dodgeBoost
        self.fenceRoof = fenceRoof
        self.zoneFree = zoneFree


class peekPlan:
    __slots__ = ["t", "tgt", "roof", "duck", "fire", "ok"]

    def __init__(self, t=0.0, tgt=0, roof=0, duck=0, fire=0, ok=False):
        self.t = t
        self.tgt = tgt
        self.roof = roof
        self.duck = duck
        self.fire = fire
        self.ok = ok


class band_fightPlan:
    __slots__ = ["r"]

    def __init__(self, r=0.0):
        self.r = r


class roofPlan:
    __slots__ = ["state", "id_", "acc", "t0", "ban", "chosen", "tries", "stepT", "waitT0", "want", "spot"]

    def __init__(
        self,
        state=0,
        id_=0,
        acc=_MISSING,
        t0=0.0,
        ban=_MISSING,
        chosen=0.0,
        tries=0,
        stepT=0.0,
        waitT0=0.0,
        want=0,
        spot=0,
    ):
        self.state = state
        self.id_ = id_
        self.acc = world.RoofAccess() if acc is _MISSING else acc
        self.t0 = t0
        self.ban = {} if ban is _MISSING else ban
        self.chosen = chosen
        self.tries = tries
        self.stepT = stepT
        self.waitT0 = waitT0
        self.want = want
        self.spot = spot

    def __copy__(self):
        other = object.__new__(type(self))
        other.state = self.state
        other.id_ = self.id_
        other.acc = copy(self.acc)
        other.t0 = self.t0
        other.ban = self.ban
        other.chosen = self.chosen
        other.tries = self.tries
        other.stepT = self.stepT
        other.waitT0 = self.waitT0
        other.want = self.want
        other.spot = self.spot
        return other


class eyeT_roofCover:
    __slots__ = ["x", "y", "z"]

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class zoneInfo:
    __slots__ = ["outNext", "outCur", "tPass", "goal", "urgent", "critical", "final", "walkable"]

    def __init__(
        self,
        outNext=0.0,
        outCur=0.0,
        tPass=0.0,
        goal=_MISSING,
        urgent=False,
        critical=False,
        final=False,
        walkable=False,
    ):
        self.outNext = outNext
        self.outCur = outCur
        self.tPass = tPass
        self.goal = [0.0] * 2 if goal is _MISSING else goal
        self.urgent = urgent
        self.critical = critical
        self.final = final
        self.walkable = walkable

    def __copy__(self):
        other = object.__new__(type(self))
        other.outNext = self.outNext
        other.outCur = self.outCur
        other.tPass = self.tPass
        other.goal = self.goal.copy()
        other.urgent = self.urgent
        other.critical = self.critical
        other.final = self.final
        other.walkable = self.walkable
        return other


class threat:
    __slots__ = ["tr", "d", "adv", "rmin", "rmax", "engaged", "dps", "phantom"]

    def __init__(self, tr=None, d=0.0, adv=0.0, rmin=0.0, rmax=0.0, engaged=False, dps=0.0, phantom=False):
        self.tr = tr
        self.d = d
        self.adv = adv
        self.rmin = rmin
        self.rmax = rmax
        self.engaged = engaged
        self.dps = dps
        self.phantom = phantom


class eyeT_findCover:
    __slots__ = ["x", "y", "z"]

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class loot:
    __slots__ = ["kind", "id_", "pos", "score", "shoot"]

    def __init__(self, kind="", id_=0, pos=_MISSING, score=0.0, shoot=False):
        self.kind = kind
        self.id_ = id_
        self.pos = [0.0] * 3 if pos is _MISSING else pos
        self.score = score
        self.shoot = shoot

    def __copy__(self):
        other = object.__new__(type(self))
        other.kind = self.kind
        other.id_ = self.id_
        other.pos = self.pos.copy()
        other.score = self.score
        other.shoot = self.shoot
        return other


def DefaultParams():
    return Params(
        Name="mech-royal",
        EngageRatio=1.25,
        DisengageRat=0.75,
        RetreatHP=0.45,
        ReturnHP=0.85,
        LeadDamp=0.65,
        GunMaxRange=224,
        StrafeMin=0.35,
        StrafeMax=1.1,
        LootRadius=220,
        WantCubes=15,
        DropGreed=0.5,
        Hunt=True,
        PracticeAware=True,
        Salt=8,
        FFAEngage=1.8,
        FFADisengage=0.95,
        FFALootRadius=140,
        FFAWantCubes=10,
        FFAReturnFire=230,
        CloseDisengage=0.8,
        DuelDisengage=0.5,
        UseRoofs=True,
        RoofMaxClimb=40,
        RoofMinHeight=12,
        RoofMinZone=60,
        ArmRadius=110,
        OpenSecs=24,
        CreditOpenS=25,
        DropRadius=300,
        LeaveTTD=10,
        UseHideMap=False,
        HideSeenW=0.6,
        HideHitW=0.9,
        HideDistW=0.16,
        HideClimbW=0.5,
        HideStick=12,
        StealthFightRange=140,
        QuietHoldS=3,
        LaserValue=6.0,
        LightningValue=2.6,
        ArmSwapMin=1.0,
        HitModel=1,
        PlanV2=True,
        KiteNeedsLaser=True,
        Brawl=True,
        AvoidAdv=1.25,
        BrawlEngage=1.3,
        BrawlDisengage=0.75,
        BrawlHunt=True,
        BrawlLootRadius=220,
        BrawlWantCubes=10,
        AvoidRange=85,
        AvoidCover=55,
        ZoneSlack=10,
        CoverFirst=True,
        NoMortar=True,
        EdgeHold=2.5,
        RunOnRange=80,
        RunOnGain=18,
        CoverMargin=8,
        ShyRange=220,
        ShyLaser=60,
        ShyMem=6,
        RetreatRunLaser=90,
        HuntLaserEdge=True,
        LootHiddenBias=0.5,
        CoverMinRange=40,
        CoverEdgeAdv=3.0,
        PeekCover=25,
        PeekReach=9,
        PeekMinRange=45,
        RoofCoverHold=6,
        RoofStandCheck=True,
        DropStick=True,
        RoofLeaveQuiet=25,
        ClimbClearRange=150,
        BrawlRoofs=True,
        LaserPreempt=True,
        LaserAimRange=285,
        AvoidCoverLaser=90,
        BrawlRoofCubes=6,
        BrawlRoofAfter=60,
        LeadPersist=True,
        LeadCum=True,
        LeadCumMin=8,
        PathFix=True,
        CreditFix=True,
        LootBoost=30,
        ProvokeRule=True,
        PlinkMaxDPS=60,
        HuntRange=130,
        HuntRangeLaser=130,
        KiteMin=130,
        KiteMax=190,
        PatientCubes=10,
        PatientRange=70,
        AntiLightningW=180,
        AntiLightningPad=12,
        SmartFireV2=True,
        LaserEarlyRel=True,
        RearBonus=0.25,
        CookoffBonus=0.30,
        CautiousT=265,
        BeamFFA=True,
        FinalHold=True,
    )


def Factory(h, w, nav):
    # Factory builds a bot with default parameters.
    return New(h, w, nav, DefaultParams())


def New(h, w, nav, p):
    b = Bot(P=p, H=h, C=h.Config, W=w, Nav=nav)
    b.rng = GoRand(int(((((h.Seed * 7919) + int(h.Slot)) + 1) + (int(p.Salt) * 104729))))
    hz = stat(h.Config.Match, "tick_hz", 20)
    if hz <= 0:
        hz = 20
    b.dt = go_div(1, hz)
    b.decide = stat(h.Config.Match, "decide_every", 2) * b.dt
    b.sizePerCube = h.Config.Cubes.SizePerCube
    b.tracks = {}
    b.crates = {}
    b.cubes = {}
    b.pickups = {}
    b.strafeSign = 1
    b.targetID = -1
    b.lootID = -1
    b.coverCell = -1
    b.deepCell, b.deepT, b.deepTryT = (-1), (-100), (-100)
    b.nearCoverT = -100
    b.standT = -100
    b.creditAbsorbT = -100
    b.holdCell = -1
    b.evadeCell = -1
    b.lastDamageT = -100
    b.lastWeaponDT = -100
    b.lastDealtT = -100
    b.lastSoundT = -100
    b.ffaSeenT = -100
    b.lastDmgBy = -1
    b.lastNpcDT = -100
    b.roamCell = -1
    b.creditT = -100
    b.lowT = -100
    b.corneredT = -100
    b.mode = "init"
    b.roof.id_ = -1
    b.roof.want, b.roof.spot = (-1), (-1)
    b.roofCoverC = -1
    b.hideCell = -1
    b.hideOutT = -100
    b.unquietT = -100
    b.slipCell, b.slipT, b.slipOnT = (-1), (-100), (-100)
    b.edgeOnT = -100
    b.jinkSign, b.jinkT = 1, (-100)
    b.roofCoverHoldT = -100
    b.peek = peekPlan(t=(-100), tgt=(-1), roof=(-1), duck=(-1), fire=(-1))
    if p.UseHideMap or p.HoldHideMap:
        b.hm = getHideMap(nav)
    b.roofFirstOK = True
    b.banUntil = {}
    b.coverT = -100
    b.evadeT = -100
    b.roofCoverT = -100
    nav.Exposure()
    nav.Components()
    nav.Roofs()
    nav.Tops()
    b.surfT = -100
    return b


def gunHitProb(d):
    # gunDPS estimates our gun damage rate at a distance against a dodging target.
    # gunHitProb is our expected gun hit rate by range. From the captured top-16 matches: with our lead
    # the shot is on the target's real path about 98% of the time under 80 m, 90% at 80-180 m and 83%
    # beyond (they hardly dodge); the 0.6 degree spread then costs a little more with distance.
    if d < 60:
        return 0.95
    elif d < 120:
        return 0.95 - ((((d - 60)) / 60) * 0.12)
    elif d < 180:
        return 0.83 - ((((d - 120)) / 60) * 0.10)
    elif d < 230:
        return 0.73 - ((((d - 180)) / 50) * 0.15)
    return 0.05


def hitTable(d, knots):
    # hitTable interpolates a hit rate over range from (distance, rate) knots.
    if d <= knots[0][0]:
        return knots[0][1]
    i = 1
    while i < go_len(knots):
        if d <= knots[i][0]:
            f = go_div(((d - knots[(i - 1)][0])), ((knots[i][0] - knots[(i - 1)][0])))
            return knots[(i - 1)][1] + (((knots[i][1] - knots[(i - 1)][1])) * f)
        i += 1
    return knots[(go_len(knots) - 1)][1]


def theirGunHitProb(d):
    # theirGunHitProb is how often a typical opponent's gun hits us at a range: measured accuracy of the
    # top-16 bots on targets that do not dodge (98/88/57/41/17% by band), reduced a little at range
    # because we do side-step what we can see coming.
    if d < 40:
        return 0.97
    elif d < 80:
        return 0.97 - ((((d - 40)) / 40) * 0.12)
    elif d < 120:
        return 0.85 - ((((d - 80)) / 40) * 0.40)
    elif d < 180:
        return 0.45 - ((((d - 120)) / 60) * 0.20)
    return 0.12


def parseHideMap(gz):
    return _decode_hide_map(gz)


def getHideMap(nav):
    # getHideMap returns the embedded map if it fits this arena (nil otherwise: callers fall back to the
    # run-time exposure estimate).
    return _load_hide_map(nav)


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def hyp(x, y):
    return math.sqrt(((x * x) + (y * y)))


def dist2(a, b):
    return hyp((a[0] - b[0]), (a[1] - b[1]))


def dist3(a, b):
    dx, dy, dz = (a[0] - b[0]), (a[1] - b[1]), (a[2] - b[2])
    return math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz)))


def angDiff(a, b):
    # angDiff returns a-b wrapped to (-pi, pi].
    d = math.fmod((a - b), (2 * math.pi))
    if d > math.pi:
        d -= 2 * math.pi
    elif d <= (-math.pi):
        d += 2 * math.pi
    return d


def norm2(x, y):
    l = hyp(x, y)
    if l < 1e-9:
        return 0, 0
    return go_div(x, l), go_div(y, l)


def stat(m, key, def_):
    if m is None:
        return def_
    v, ok = m.get(key, 0.0), key in m
    if ok:
        return v
    return def_


def approach2(cx, cy, tx, ty, maxDelta):
    # approach moves cur toward target by at most maxDelta (vector form).
    dx, dy = (tx - cx), (ty - cy)
    d = hyp(dx, dy)
    if (d <= maxDelta) or (d < 1e-12):
        return tx, ty
    return (cx + (go_div(dx, d) * maxDelta)), (cy + (go_div(dy, d) * maxDelta))


def segPointDist2D(px, py, ax, ay, bx, by):
    # segPointDist2D returns the distance from point p to segment a-b and the parameter of the closest point.
    ex, ey = (bx - ax), (by - ay)
    l2 = (ex * ex) + (ey * ey)
    t = 0.0
    if l2 > 1e-12:
        t = clamp(go_div((((((px - ax)) * ex) + (((py - ay)) * ey))), l2), 0, 1)
    cx, cy = (ax + (ex * t)), (ay + (ey * t))
    return hyp((px - cx), (py - cy)), t


def v074(p):
    # v074 restores the parameters of the published v0.7.4.
    p.RetreatRunMax = 0
    p.CreditOpenS = 0
    p.ShySecs = 0
    p.SlotRule = False


def oldLead(p):
    # oldLead is the gun lead of every build up to v0.6.1: instantaneous velocity, damped to 75%.
    p.LeadDamp = 0.75
    p.LeadPersist = False
    p.LeadCum = False


def v061(p):
    # v061 restores the parameters of the published v0.6.1.
    brawl2(p)
    p.LootBoost = 0
    p.ProvokeRule = False
    p.PlinkMaxDPS = 0
    p.CreditFix = False
    p.ZoneSlack = 0
    p.BrawlWantCubes = 15
    p.BrawlRoofs = False
    p.LaserPreempt = False
    p.LaserAimRange = 0
    p.AvoidCoverLaser = 0
    p.RoofLeaveQuiet = 0
    p.DropStick = False
    p.CoverFirst = False
    p.HuntLaserEdge = False
    p.LootHiddenBias = 0
    p.EdgeHold = 0
    p.NoMortar = False
    p.RunOnRange = 0
    p.CoverMargin = 0
    p.RetreatRunMax = 0
    p.CreditOpenS = 0
    oldLead(p)


def v07(p):
    # v07 restores the parameters of the published v0.7.
    p.CoverFirst = False
    p.HuntLaserEdge = False
    p.LootHiddenBias = 0
    p.EdgeHold = 0
    p.NoMortar = False
    p.RunOnRange = 0
    p.CoverMargin = 0
    p.RetreatRunMax = 0
    p.CreditOpenS = 0


def brawl2(p):
    # brawl2 is the armed-farmer parameter set (the defaults since v0.6): the published practice behaviour
    # (squad stance after the opening) with the stealth stances replaced.
    p.Brawl = True
    p.HitModel = 1
    p.PlanV2 = True
    p.KiteNeedsLaser = True
    p.LaserValue = 6
    p.AvoidAdv = 1.25


def brawl(p):
    # brawl is the always-fight parameter set built after the first real matches.
    p.PracticeAware = False
    p.HitModel = 1
    p.PlanV2 = True
    p.KiteNeedsLaser = True
    p.LaserValue = 6


Trace = go_getenv("MECH_TRACE") != ""
Stats = go_getenv("MECH_STATS") != ""
realMyGun = [[30, 0.95], [60, 0.86], [100, 0.55], [150, 0.28], [200, 0.18], [230, 0.12]]
realTheirGun = [[30, 0.92], [60, 0.78], [100, 0.57], [150, 0.32], [200, 0.15], [230, 0.10]]


def _tmp_205():
    d = [[0.0] * 2 for _ in range(16)]
    i = 0
    while i < 16:
        a = (float(i) * math.pi) / 8
        d[i] = [math.cos(a), math.sin(a)]
        i += 1
    return (d).copy()


dirs16 = _tmp_205()
upgradeRank = {
    "plating": 1.00,
    "armor": 0.96,
    "gun_rate": 0.90,
    "gun_damage": 0.88,
    "gun_velocity": 0.80,
    "laser_damage": 0.91,
    "laser_charge": 0.86,
    "lightning_efficiency": 0.92,
    "lightning_range": 0.87,
    "nanites": 0.72,
    "servos": 0.76,
    "reactor": 0.50,
    "capacitor": 0.45,
    "gun_mag": 0.60,
    "sensors": 0.35,
    "gyros": 0.30,
    "jets": 0.30,
    "mortar_reload": 0.42,
    "mortar_splash": 0.45,
    "mortar_velocity": 0.40,
    "lightning_chain": 0.40,
    "laser_pierce": 0.20,
}


def _decode_hide_map(blob):
    raw = gzip.decompress(blob)
    h = hideMap()
    if len(raw) < 24 or raw[:4] != b"HM3\n":
        return h
    h.nx, h.ny, h.step, h.lw, h.lh = struct.unpack_from("<5i", raw, 4)
    size = h.lw * h.lh
    if h.step <= 0 or size <= 0 or len(raw) < 24 + size * 3:
        return h
    body = raw[24 : 24 + size * 3]
    h.class_ = body[::3]
    squares = [go_f32(go_f32(x / 255) ** 2) for x in range(256)]
    h.seen = [squares[x] for x in body[1::3]]
    h.hit = [squares[x] for x in body[2::3]]
    for i, value in enumerate(h.class_):
        if value == hmNone:
            continue
        cx = (i % h.lw) * h.step + h.step // 2
        cy = (i // h.lw) * h.step + h.step // 2
        if cx < h.nx and cy < h.ny:
            h.cells.append(cy * h.nx + cx)
    h.ok = True
    return h


def _load_hide_map(nav):
    h = _decode_hide_map(Path(__file__).with_name("hidemap.gz").read_bytes())
    if not h.ok or (h.nx, h.ny) != (nav.NX, nav.NY):
        return None
    inspected = h.cells[::97]
    errors = sum((h.class_[h.lat(k)] == hmRoof) != nav.Solid[k] for k in inspected)
    return h if inspected and errors * 20 <= len(inspected) else None
