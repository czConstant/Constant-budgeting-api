package main

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"runtime/debug"

	"github.com/getsentry/raven-go"
	"github.com/jinzhu/gorm"
	"github.com/pkg/errors"

	"github.com/czConstant/constant-budgeting-api/apis"
	"github.com/czConstant/constant-budgeting-api/configs"
	"github.com/czConstant/constant-budgeting-api/daos"
	"github.com/czConstant/constant-budgeting-api/databases"
	"github.com/czConstant/constant-budgeting-api/logger"
	"github.com/czConstant/constant-budgeting-api/services"
	"github.com/czConstant/constant-budgeting-api/services/3rd/backends"
	"github.com/czConstant/constant-budgeting-api/services/3rd/mailer"
	"github.com/czConstant/constant-core/pkg/core"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func init() {
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}
}

func main() {
	conf := configs.GetConfig()
	logger.NewLogger("spend-api", conf.LogPath, true)
	defer logger.Sync()
	raven.SetDSN(conf.RavenDNS)
	raven.SetEnvironment(conf.RavenENV)
	defer func() {
		if err := recover(); err != nil {
			panicErr := errors.Wrap(errors.New("panic start server"), string(debug.Stack()))
			raven.CaptureErrorAndWait(panicErr, nil)
			logger.Info(
				logger.LOGGER_API_APP_PANIC,
				"panic start server",
				zap.Error(panicErr),
			)
			return
		}
	}()

	var migrateDBMainFunc func(db *gorm.DB) error
	// migrateDBMainFunc = databases.MigrateDBMain
	dbMain, err := databases.Init(
		conf.DbURL,
		migrateDBMainFunc,
		10,
		20,
		conf.Debug,
	)
	if err != nil {
		panic(err)
	}
	daos.InitDBConn(
		dbMain,
	)
	mailer.SetURL(conf.Mailer.URL)
	var (
		core = core.Init(conf.Core.URL)
		//new 3rd services
		bc = &backends.Client{
			BaseURL: conf.Backend.URL,
		}

		// new services
		us = services.NewUser(
			core,
			bc,
		)
	)

	r := gin.Default()
	srv := apis.NewServer(
		r,
		us,
	)
	srv.Routers()
	if conf.Port == 0 {
		conf.Port = 8080
	}
	if err := r.Run(fmt.Sprintf(":%d", conf.Port)); err != nil {
		logger.WrapError(
			logger.LOGGER_API_APP_ERROR,
			err,
		)
	}
}
