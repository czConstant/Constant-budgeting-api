package serializers

import (
	"time"
)

type AuthTokenResp struct {
	Token     string    `json:"token"`
	ExpiredAt time.Time `json:"expired_at"`
}
