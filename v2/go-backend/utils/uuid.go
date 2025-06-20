package utils

import (
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jxskiss/base62"
)

// GenerateUUIDv7Base62 generates a time-based UUID (v7), removes dashes, and encodes it to Base62
func GenerateUUIDv7(ident string) string {
	// Get the current Unix timestamp in milliseconds
	now := time.Now().UnixMilli()

	// Create a new UUID based on the current time and random data
	uuidBytes := make([]byte, 16)
	copy(uuidBytes[0:8], []byte(fmt.Sprintf("%016x", now)))

	// Generate random data for the remaining part
	randUUID := uuid.New()
	copy(uuidBytes[8:], randUUID[:8])

	// Set version to 7 (time-based UUID)
	uuidBytes[6] = (uuidBytes[6] & 0x0f) | (0x70) // Set the version to 7 (bits 6-7)

	// Set variant to 2 (RFC4122)
	uuidBytes[8] = (uuidBytes[8] & 0x3f) | 0x80 // Set the variant (bits 8-9)

	// Create UUID and convert to string (with dashes)
	uuidWithoutDashes := uuid.Must(uuid.FromBytes(uuidBytes)).String()

	// Remove dashes from the UUID string
	uuidClean := strings.ReplaceAll(uuidWithoutDashes, "-", "")

	// Encode the UUID without dashes in Base62
	base62Encoded := base62.EncodeToString([]byte(uuidClean))

	// Prepend the custom prefix
	return ident + "_" + base62Encoded
}
