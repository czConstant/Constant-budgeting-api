package mailer

import (
	"fmt"
	"net/http"

	"github.com/czConstant/constant-budgeting-api/helpers"
)

type Contact struct {
	Name    string
	Address string
}

type SendRequest struct {
	Type string
	Lang string
	From Contact
	To   Contact
	Bccs []string
	Ccs  []string
	Data interface{}
}

var mailer *Mailer

func init() {
	mailer = &Mailer{}
}

func SetURL(apiURL string) {
	mailer.SetURL(apiURL)
}

func Send(
	fromAddress string,
	fromName string,
	toAddress string,
	toName string,
	typeStr string,
	lang string,
	data interface{},
	ccs []string,
	bccs []string,
) error {
	return mailer.Send(
		fromAddress,
		fromName,
		toAddress,
		toName,
		typeStr,
		lang,
		data,
		ccs,
		bccs,
	)
}

type Mailer struct {
	apiURL   string
	sendFunc func(
		fromAddress string,
		fromName string,
		toAddress string,
		toName string,
		typeStr string,
		lang string,
		data interface{},
		ccs []string,
		bccs []string,
	) error
}

func (m *Mailer) SetURL(apiURL string) {
	m.apiURL = apiURL
}

func NewMailer(
	apiURL string,
	sendFunc func(
		fromAddress string,
		fromName string,
		toAddress string,
		toName string,
		typeStr string,
		lang string,
		data interface{},
		ccs []string,
		bccs []string,
	) error,
) *Mailer {
	return &Mailer{apiURL, sendFunc}
}

func (m *Mailer) Send(
	fromAddress string,
	fromName string,
	toAddress string,
	toName string,
	typeStr string,
	lang string,
	data interface{},
	ccs []string,
	bccs []string,
) error {
	if m.sendFunc != nil {
		return m.sendFunc(
			fromAddress,
			fromName,
			toAddress,
			toName,
			typeStr,
			lang,
			data,
			ccs,
			bccs,
		)
	}
	postData := SendRequest{
		From: Contact{
			Address: fromAddress,
			Name:    fromName,
		},
		To: Contact{
			Address: toAddress,
			Name:    toName,
		},
		Type: typeStr,
		Lang: lang,
		Data: data,
		Ccs:  ccs,
		Bccs: bccs,
	}
	err := helpers.CurlURL(
		fmt.Sprintf("%s/%s", m.apiURL, "request"),
		http.MethodPost,
		nil,
		postData,
		nil,
		false,
	)
	if err != nil {
		return err
	}
	return nil
}
