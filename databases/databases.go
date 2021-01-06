package databases

import (
	_ "github.com/go-sql-driver/mysql"
	"github.com/jinzhu/gorm"
	"github.com/pkg/errors"
)

// Init : config
func Init(dbURL string, migrateFunc func(db *gorm.DB) error, idleNum int, openNum int, debug bool) (*gorm.DB, error) {
	dbConn, err := gorm.Open("mysql", dbURL)
	if err != nil {
		return nil, errors.Wrap(err, "gorm.Open")
	}
	dbConn.LogMode(debug)
	dbConn = dbConn.Set("gorm:save_associations", false)
	dbConn = dbConn.Set("gorm:association_save_reference", false)
	dbConn.DB().SetMaxIdleConns(idleNum)
	dbConn.DB().SetMaxOpenConns(openNum)
	if migrateFunc != nil {
		err = migrateFunc(dbConn)
		if err != nil {
			return dbConn, err
		}
	}
	return dbConn, nil
}

func MigrateDBMain(db *gorm.DB) error {
	allTables := []interface{}{}
	if err := db.AutoMigrate(allTables...).Error; err != nil {
		return errors.Wrap(err, "db.AutoMigrate")
	}
	return nil
}
