package services

import (
	"github.com/czConstant/constant-budgeting-api/errs"
	"github.com/czConstant/constant-budgeting-api/logger"
	"github.com/czConstant/constant-budgeting-api/models"
	"github.com/czConstant/constant-budgeting-api/services/3rd/backends"
	"github.com/czConstant/constant-core/domain"
	"github.com/czConstant/constant-core/pkg/core"
)

type User struct {
	core *core.Core
	bc   *backends.Client
}

func NewUser(
	core *core.Core,
	bc *backends.Client,
) *User {
	return &User{
		core: core,
		bc:   bc,
	}
}

func (us *User) GetUserMe(token string) (*models.User, int, error) {
	var err error
	m, httpCode, err := us.bc.GetUserCheck(token)
	if err != nil {
		return nil, httpCode, logger.WrapStacktraceError(errs.ErrorWithMessage(errs.ErrSystemError, err.Error()))
	}
	return m, 0, nil
}

func (us *User) GetCoreUser(userID uint) (*domain.User, error) {
	user, err := us.core.User.FindByID(userID, []string{})
	if err != nil {
		return nil, logger.WrapStacktraceError(errs.ErrorWithMessage(errs.ErrSystemError, err.Error()))
	}
	return user, nil
}

func (us *User) GetAvailableBalance(token string) (uint64, error) {
	return us.bc.GetAvailableBalance(token)
}
