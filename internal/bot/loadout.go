package bot

import (
	"math"

	"apexbot/internal/proto"
)

// cycleGain measures the change in sustained gun damage, including reload time.
func cycleGain(magazine, cooldown, reload, nextMagazine, nextCooldown, nextReload float64) float64 {
	oldPeriod := cooldown + reload/magazine
	newPeriod := nextCooldown + nextReload/nextMagazine
	return oldPeriod/newPeriod - 1
}

// Give the first drum priority when repeated reloads would consume a large
// portion of firing time. Later magazines and faster reloads reduce its value.
func (b *Bot) upgradeValue(id string) float64 {
	value, known := upgradeRank[id]
	if !known {
		return 0.25
	}
	switch id {
	case "gun_mag":
		if slot := b.has("gun"); slot >= 0 {
			stats := b.slots[slot].stats
			mag := math.Max(1, stat(stats, "mag", 12))
			cooldown := math.Max(0.01, stat(stats, "cooldown", 0.24))
			reload := math.Max(0, stat(stats, "reload", 2.4))
			gain := cycleGain(mag, cooldown, reload, mag+8, cooldown, 0.8*reload)
			value += gain
		}
	case "reactor", "capacitor":
		if b.has("lightning") >= 0 {
			value += 0.3
		}
	case "nanites":
		value += math.Max(0, b.P.NanoBoost)
	}
	return value
}

func (b *Bot) pickUpgrade(action *proto.Action) {
	offer := b.o.Offer
	if offer == nil || len(offer.Choices) == 0 {
		return
	}
	best := 0
	value := b.upgradeValue(offer.Choices[0].ID)
	for i := 1; i < len(offer.Choices); i++ {
		next := b.upgradeValue(offer.Choices[i].ID)
		if next > value {
			best, value = i, next
		}
	}
	action.Pick = best
}
