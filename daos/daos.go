package daos

import (
	"fmt"

	"github.com/czConstant/constant-budgeting-api/logger"
	"github.com/getsentry/raven-go"
	"github.com/jinzhu/gorm"
	"github.com/pkg/errors"
)

var (
	dbMain *gorm.DB
)

func InitDBConn(dbMainConn *gorm.DB) {
	dbMain = dbMainConn
}

func GetDBMain() *gorm.DB {
	return dbMain
}

func WithTransaction(dbConn *gorm.DB, callback func(*gorm.DB) error) (err error) {
	tx := dbConn.Begin()
	defer func() {
		if rval := recover(); rval != nil {
			tx.Rollback()
			rvalStr := fmt.Sprint(rval)
			err = fmt.Errorf(rvalStr)
			raven.CaptureError(err,
				nil,
				raven.NewException(errors.New(rvalStr), raven.NewStacktrace(2, 3, nil)),
			)
			logger.WrapCaptureError(errors.New(rvalStr))
		}
	}()
	if err = callback(tx); err != nil {
		tx.Rollback()
		return err
	}
	if err := tx.Commit().Error; err != nil {
		return errors.Wrap(err, "tx.Commit()")
	}
	return err
}

type SpendDAO struct {
}

func (d *SpendDAO) Create(tx *gorm.DB, m interface{}) error {
	if err := tx.Create(m).Error; err != nil {
		return err
	}
	return nil
}

func (d *SpendDAO) Save(tx *gorm.DB, m interface{}) error {
	if err := tx.Save(m).Error; err != nil {
		return err
	}
	return nil
}

func (d *SpendDAO) Delete(tx *gorm.DB, m interface{}) error {
	if err := tx.Delete(m).Error; err != nil {
		return err
	}
	return nil
}

func (d *SpendDAO) first(tx *gorm.DB, m interface{}, filters map[string][]interface{}, preloads map[string][]interface{}, orders []string, forUpdate bool) error {
	query := tx
	for k, v := range filters {
		if v != nil {
			query = query.Where(k, v...)
		} else {
			query = query.Where(k)
		}
	}
	for k, v := range preloads {
		if v != nil {
			query = query.Preload(k, v...)
		} else {
			query = query.Preload(k)
		}
	}
	if orders != nil && len(orders) > 0 {
		for _, v := range orders {
			query = query.Order(v)
		}
	}
	if forUpdate {
		query = query.Set("gorm:query_option", "FOR UPDATE")
	}
	if err := query.First(m).Error; err != nil {
		return err
	}
	return nil
}

func (d *SpendDAO) find(tx *gorm.DB, ms interface{}, filters map[string][]interface{}, preloads map[string][]interface{}, orders []string, forUpdate bool) error {
	query := tx
	for k, v := range filters {
		if v != nil {
			query = query.Where(k, v...)
		} else {
			query = query.Where(k)
		}
	}
	for k, v := range preloads {
		if v != nil {
			query = query.Preload(k, v...)
		} else {
			query = query.Preload(k)
		}
	}
	if orders != nil && len(orders) > 0 {
		for _, v := range orders {
			query = query.Order(v)
		}
	}
	if forUpdate {
		query = query.Set("gorm:query_option", "FOR UPDATE")
	}
	if err := query.Find(ms).Error; err != nil {
		return err
	}
	return nil
}

func (d *SpendDAO) count(tx *gorm.DB, m interface{}, filters map[string][]interface{}) (uint, error) {
	query := tx
	for k, v := range filters {
		if v != nil {
			query = query.Where(k, v...)
		} else {
			query = query.Where(k)
		}
	}
	var count uint
	if err := query.Model(m).Count(&count).Error; err != nil {
		return 0, err
	}
	return count, nil
}
