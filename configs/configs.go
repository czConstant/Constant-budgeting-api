package configs

import (
	"encoding/json"
	"os"

	"github.com/czConstant/constant-evn/client"
)

var config *Config

func init() {
	file, err := os.Open("configs/config.json")
	if err != nil {
		panic(err)
	}
	decoder := json.NewDecoder(file)
	v := Config{}
	err = decoder.Decode(&v)
	if err != nil {
		panic(err)
	}
	config = &v
	evnClient := &client.Client{
		URL: config.EvnURL,
	}

	dbURL, _, err := evnClient.GetSecret("DB-BACKEND-URL")
	if err != nil {
		panic(err)
	}
	config.DbURL = client.ParseDBURL(dbURL)
}

func GetConfig() *Config {
	return config
}

type Config struct {
	Env      string `json:"env"`
	EvnURL   string `json:"evn-url"`
	RavenDNS string `json:"raven_dns"`
	RavenENV string `json:"raven_env"`
	Port     int    `json:"port"`
	LogPath  string `json:"log_path"`
	DbURL    string
	Debug    bool `json:"debug"`
	Mailer   *struct {
		URL string `json:"url"`
	} `json:"mailer"`
	Backend *struct {
		URL string `json:"url"`
	} `json:"backend"`
	Core *struct {
		URL string `json:"url"`
	} `json:"core"`
}
