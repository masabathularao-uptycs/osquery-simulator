package main
import (
"fmt"
"math/rand"
"sync"
"time"
)

var wg sync.WaitGroup

func main() {
wg.Add(2)
fmt.Println("start Goroutines")
go printCounts("A",10)
go printCounts("B",20)
fmt.Println("Wait to finish Goroutines")
wg.Wait()

fmt.Println("\n terminating programming")



}

func printCounts(lable string, cct int) {
defer wg.Done()
for count := 1; count < cct; count++ {

sleep := rand.Int63n(1000)
time.Sleep(time.Duration(sleep)*time.Millisecond)

fmt.Printf(" count: %d from %s\n",count,lable)
}

}