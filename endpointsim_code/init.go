package main

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"math"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	uuid "github.com/nu7hatch/gouuid"
)

func init() {
	flag.Parse()
	if *domain_flag == "" || *secret_flag == "" || *name_flag == "" || *port_flag == "" || *count_flag == 0 {
		log.Fatalf("Please provide all flags of domain, secret, name, count, and port")
	}
	domain = *domain_flag
	secret = *secret_flag
	name = *name_flag
	port = *port_flag
	count = *count_flag
	enrollurl = fmt.Sprintf("https://%s.uptycs.dev/agent/enroll", domain)
	configurl = fmt.Sprintf("https://%s.uptycs.dev/agent/config", domain)
	logurl = fmt.Sprintf("https://%s.uptycs.dev/agent/log", domain)
	distributedreadurl = fmt.Sprintf("https://%s.uptycs.dev/agent/distributed_read", domain)
	distributedwriteurl = fmt.Sprintf("https://%s.uptycs.dev/agent/distributed_write", domain)
	enrollReqTimeout = 30
	configInterval = 300
	distInterval = 200
	distributedDistInterval = 10

	set_dist_write_stats()
	// disable logging
	gin.SetMode(gin.ReleaseMode)
	gin.DefaultWriter = ioutil.Discard
	set_log()
	parse_names()
	m := new(sync.Map)
	node_key = m
	num_log_channels = int(math.Ceil(float64(float64(count) / float64(assets_per_log_channel))))
	log.Println("Count:", count, "num_log_channels:", num_log_channels)

	for x := 0; x < num_log_channels; x++ {
		c := make(chan LogGoRoutineMsg)
		log_channels = append(log_channels, c)
		go log_msg_listener(c)
	}

	for x := 0; x < config_channel_count; x++ {
		c := make(chan ConfigRequest)
		config_channels = append(config_channels, c)
		go config_listener(c)
	}

	if allow_reads {
		//fmt.Println("dist_read_channel_count",dist_read_channel_count)
		for x := 0; x < dist_read_channel_count; x++ {
			c := make(chan DistReadRequest)
			//fmt.Println(x,"inside allow_reads",c)
			dist_read_channels = append(dist_read_channels, c)

			go dist_read_listener(c)
			//fmt.Println(x,"inside allow_reads",c,len(dist_read_channels))
		}
	}

	caCert, certErr := ioutil.ReadFile("ca.crt")
	if certErr != nil {
		log.Fatal(certErr)
	}
	caCertPool.AppendCertsFromPEM(caCert)
	set_http_clients()
}

func log_msg_listener(c chan LogGoRoutineMsg) {
	for msg := range c {
		log_goroutine(msg.ToPost, msg.Client)
	}
}

func config_listener(c chan ConfigRequest) {
	for CR := range c {
		config_goroutine(CR.NodeKey, CR.Index, CR.HttpChan, CR.HttpClient)
	}
}

func set_log() {
	logfile_name := "osx_log" + string(port) + ".out"
	os.Remove(logfile_name)
	logFile, err := os.OpenFile(logfile_name, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0666)
	if err != nil {
		panic(err)
	}
	mw := io.MultiWriter(os.Stdout, logFile)
	log.SetOutput(mw)
}

func set_http_clients() {
	for x := 0; x < count; x++ {
		e := new_http_client(time.Second * enrollReqTimeout)
		enrollClients = append(enrollClients, e)
		c := new_http_client(time.Second * enrollReqTimeout)
		configClients = append(configClients, c)
		l := new_http_client(time.Second * 180)
		logClients = append(logClients, l)
		if allow_reads {
			//r := new_http_client(time.Second * distributedDistInterval)
			r := new_http_client(time.Second * 120)
			distReadClients = append(distReadClients, r)
		}
	}
}

func new_http_client(timeout time.Duration) *http.Client {
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				RootCAs:            caCertPool,
				InsecureSkipVerify: true,
			},
			DialContext: (&net.Dialer{
				Timeout:   120 * time.Second,
				KeepAlive: 0 * time.Second,
			}).DialContext,
		},
		Timeout: timeout,
	}
	return client
}

func set_dist_write_stats() {
	dist_write_status["info"] = "0"
	m := make(map[string]string)
	m["days"] = "60"
	m["hours"] = "7"
	m["minutes"] = "29"
	m["seconds"] = "5"
	m["total_seconds"] = "5210945"
	dist_write_table = append(dist_write_table, m)
}

func parse_names() {
	file, err := os.Open(name)
	if err != nil {
		log.Fatalf("Could not open file %s", name)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	name_count := 0
	for scanner.Scan() {
		if name_count < count {
			random_names = append(random_names, scanner.Text())
			uuid, uerr := uuid.NewV4()
			if uerr != nil {
				log.Fatalf("Got error generating uuid: %v", uerr)
			}

			random_uuids = append(random_uuids, strings.ToUpper(uuid.String()))
			name_count += 1
		} else {
			break
		}

	}
	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}
}

func dist_read_listener(c chan DistReadRequest) {
	for distMsg := range c {
		node_key := get_node_key(distMsg.Index)
		//fmt.Println("node_key",node_key,"daya",distMsg.Index)
		client := distMsg.HttpClient
		//fmt.Println("client",client,distributedreadurl)
		ee := &distReadReq{NodeKey: node_key + ":" + random_names[distMsg.Index]}
		eej, _ := json.Marshal(ee)
		req, brr := http.NewRequest("POST", distributedreadurl, bytes.NewBuffer(eej))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "osquery/4.6.6.18-Uptycs")
		req.Header.Set("Accept", "application/json")

		if brr != nil {
			log.Fatal("Error reading request. brr", brr)
		}
		// Set headers
		//fmt.Println(req)
		start_req := time.Now()
		resp, err := client.Do(req)
		if err != nil {
			log.Fatal("Error reading response. err", err)
			continue
		}
		elapsed := time.Since(start_req).Milliseconds()

		dist_read_histogram.add(float32(elapsed), &config_histogram_mux)

		var outer map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&outer)
		resp.Body.Close()
		if len(outer) > 0 {
			for key, value := range outer {
				if key == "queries" {
					//fmt.Println("key",key,"value",value)
					query_map := value.(map[string]interface{})
					for query, _ := range query_map {
						query_portion := make(map[string]interface{})
						to_respond := make(map[string]interface{})
						query_portion[query] = dist_write_table
						to_respond["queries"] = query_portion
						to_respond["node_key"] = node_key
						to_respond["statuses"] = dist_write_status
						response_body, err := json.Marshal(to_respond)
						if err != nil {
							log.Fatalf("Got distributed_write error %s", err)
						}
						start_dw := time.Now()
						dw, dw_e := client.Post(distributedwriteurl, "application/json", bytes.NewBuffer(response_body))
						if dw_e != nil {
							log.Fatalf("Got distributed write error %s", dw_e)
						}
						dw_elapsed := time.Since(start_dw).Milliseconds()
						dist_write_histogram.add(float32(dw_elapsed), &dist_write_mux)
						if dw.Status != "200 OK" {
							dist_write_fail_counter += 1
							log.Println("Failed distributed_write for index", distMsg.Index)
						}
						json.NewDecoder(dw.Body).Decode(&resp)
						dw.Body.Close()
					}
				}
			}
		}
		scanner := bufio.NewScanner(resp.Body)
		scanner.Split(bufio.ScanBytes)
		for scanner.Scan() {
			fmt.Print(scanner.Text())
		}
		distMsg.HttpChan <- &HttpResponse{distributedreadurl, resp, err}
	}
}
