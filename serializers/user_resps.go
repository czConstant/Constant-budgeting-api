package serializers

import "github.com/czConstant/constant-budgeting-api/models"

type UserResp struct {
	ID    uint   `json:"id"`
	Email string `json:"email"`
}

func NewUserResp(m *models.User) *UserResp {
	if m == nil {
		return nil
	}
	return &UserResp{
		ID:    m.ID,
		Email: m.Email,
	}
}

func NewUserRespArr(ms []*models.User) []*UserResp {
	resps := []*UserResp{}
	for _, m := range ms {
		resps = append(resps, NewUserResp(m))
	}
	return resps
}
