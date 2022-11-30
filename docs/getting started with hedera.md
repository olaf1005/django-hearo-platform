!e[https://hedera.com](https://cdn.frontify.com/api/screen/thumbnail/eYJA2myblmInvdfPogN-Bk6PpLDYBMJfo_wUyU8AjLzM-PigLcgvyVV39Qt96LheiBJwbDiSgFu3Q2ci3qT2IA/1360)

# Getting Started with Hedera 

### Getting connected through the [Hedera portal](https://go.hedera.com)

#### ID Verification

We want to allow devs to earn __ℏ__ by using our APIs. In order to be allowed to do this under US law we need to verify your identity on the [Hedera Portal](https://go.hedera.com). This process is explained in detail in [this video](https://youtu.be/1pJRNOde9Vw).

_Should the automated identity verification fail, please email compliance@hedera.com with your name and email used to create your account._

#### Getting access to a Hedera testnet

For illustrative purposes, the examples below use the Hedera Go SDK. You can use whichever of the Hedera SDKs you prefer. If you prefer, you can watch a [video walkthrough](https://youtu.be/0O0-Vie6v5U) of these steps to get you connected and make your first micro-payment.

##### 1. Create a Hedera account

- Complete the ID verification process (see above)

##### 2. Enter your testnet access code to your Hedera Account

- Testnet access codes are provided at Meetups and hackathon events. If you do not have a testnet access code you can register your interest via a link in the Hedera portal.eted registration.

##### 3. Get your environment configured

- Create a folder for your repo. In terminal: `mkdir hedera-z2m` followed my `cd hedera-z2m`
- So that you don't have to build your entire codebase from scratch make sure you have git-lfs installed. In terminal: `brew install git-lfs`
- Initialise a new module in Go. In terminal `go mod init github.com/<username>/hedera-z2m` making sure that you replace `<username>` with your own github username.
- Use your IDE of choice to manipulate source code in subsequent steps. In the Hedera DA team both [VSCode](https://code.visualstudio.com/docs/languages/go) and [GoLand](https://www.jetbrains.com/go/) are commonly used.

##### 4. Create your public/private keypair

- You can achieve this easily with the following go code (see file `keys.go` attached to this gist)

```go
package main

import (
  "fmt"

  "github.com/hashgraph/hedera-sdk-go"
)

func main() {
  secret := hedera.GenerateSecretKey()
  fmt.Printf("secret = %v\n", secret)

  public := secret.Public()
  fmt.Printf("public = %v\n", public)
}
```

- Execute this code from terminal, using `go run keys.go`
- Make a note of both of the keys output generated. For a testnet you can copy and paste the keys into a text file, although for security reasons you should ___never do this for mainnet___.

##### 5. Paste your _public_ key into the Hedera portal to complete the testnet registration process

- There are several key items shown in the Hedera portal. Keep the Hedera portal open or make a node of these items so that you can connect to the testnet:
  - Your Hedera __Account ID__ for this testnet – e.g. `0:0:1099`
  - The __testnet Address__ and __Port__ – e.g. `testnet.hedera.com:50123`
  - The Hedera __Node ID__ – e.g. `0:0:3`

  All Hedera IDs consist of three long-integers separated by colons. The three numbers represent `Shard-number`, `Realm number` and `Account number` respectively. Shards and Realms are not yet in use so expect the first two numbers to be zeros.

##### 6. Your first Hedera application – Check your account balance

All of the code explained from here to the end of Step 9 is contained within the file `main.go` attached to this gist)

- Create a new `main.go` file as follows:

```go
package main

import (
  "fmt"
  "time"
****
  "github.com/hashgraph/hedera-sdk-go"
)

func main() {
```

  Establish connection to the Hedera node by using the __testnet Address__ and __Port__ shown in the Hedera portal. Be sure to replace the example `50123` to your specific port.

  Defer the disconnection of the connection to guarantee a clean disconnect from the node.

```go
  client := hedera.Dial("testnet.hedera.com:50123")
  defer client.Close()
```

  Initialise the `myAccount` variable based on your __Account ID__ from the portal. Ensure that you replace the example `1099` with your own Account ID.

```go
  myAccount := hedera.NewAccountID(0, 0, 1099)
```

  Check your account balance. `GetAccountBalance` constructs the request; adding `.Answer()` executes the request. Don't forget error-handling.

  `fmt.Printf` can then output the balance.

```go
  myBalance, err := client.GetAccountBalance(myAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Your balance: %v \n", myBalance)
```

  Finally, close the braces for `func main`.

```go
}
```

- You should now be able to run your first Hedera program by executing `go run main.go` from terminal.

- If everything goes according to plan you should see `Your balance; 10000` which represents the initial number of _hbars_ in your testnet account.

##### 7. A note on testnet throttling

- For hackathon purposes, testnets have been throttled, allowing a limited number of Hedera transactions per account per second. Hackathon-specific testnet configuration is further described in a section later in this document.

- In order to accommodate testnet throttling, it's necessary to add a short delay between transactions issued to the Hedera node. To add a one second delay, use the following code:

```go
  time.Sleep(1 * time.Second)
```

- If such delays are not included between transactions, it is likely that `transaction failed the pre-check: Busy` errors will be observed upon execution.

##### 8. Improve your application – check your friend's account balance

- If you know the account ID of another account on your testnet – perhaps a friend or colleague – you can also check their balance. If your friends won’t share their accounts, or if you don’t have any friends, see the `account.go` file attached to this gist in order to create additional accounts.

- For the purposes of this example, an Account ID of `0:0:1100` will be used for that second account. Don't forget to amend `1100` to the account number of your friend's account. Failing to do this will likely result in a `transaction failed the pre-check: InvalidAccount` message.

- To continue with the example, add the following code into `func main` before the closing braces:

  Before executing any transfers, you can initialise a second variable `friendAccount` representing the second account, query its balance and output the result.

```go
  friendAccount := hedera.NewAccountID(0, 0, 1100)

  friendBalance, err = client.GetAccountBalance(friendAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Friend balance: %v \n", friendBalance)
```

  Once again, a delay is be added to accommodate testnet throttling. For brevity, this statement will be included _without further comment_ in all subsequent examples.

```go
  time.Sleep(1 * time.Second)
```

- Run the program again by executing `go run main.go` from terminal.

- Assuming that neither account has made any transfers so far, you should see `Your balance; 10000` followed by `Friend balance; 10000` as the initial number of _hbars_ in both testnet account is the same.

##### 9. Extend your application – transfer _hbars_ from your account to your friend's account

- Your __secret__ key (also known as _private_ key) is required in order to transfer _hbars_ out of your account. You should have noted this when it was generated in Step 4 of this process (above).

- The term "operator" used in the naming of the next variable `operatorSecret` is used to highlight the fact that this is the account responsible for submitting the transaction. Ensure that your replace `<my-secret-key>` with your own secret key in the following code block:

```go
  operatorSecret, err := hedera.SecretKeyFromString("<my-secret-key>")
  if err != nil {
    panic(err)
  }
```

  The next statement is more complex as it takes advantage of the builder pattern. The statement is included in its entirety; each line is explained individually below. Take care to replace `1099` with your account number and `1100` with your friend's account number.

```go
  response, err := client.CryptoTransfer().
    Operator(hedera.NewAccountID(0, 0, 1099)).
    Node(hedera.NewAccountID(0, 0, 3)).
    Transfer(hedera.NewAccountID(0, 0, 1099), -1).
    Transfer(hedera.NewAccountID(0, 0, 1100), 1).
    Sign(operatorSecret).
    Sign(operatorSecret).
    Execute()
    if err != nil {
      panic(err)
    }
```

- Line __1__: `response, err := client.CryptoTransfer().` creates a transaction to transfer _hbars_ between accounts.

- Line __2__: `Operator(hedera.NewAccountID(0, 0, 1099)).` identifies the account initiating the transaction.

- Line __3__: `Node(hedera.NewAccountID(0, 0, 3)).` identifies the account of the Hedea node to which the transaction is being sent.

- Line __4__: `Transfer(hedera.NewAccountID(0, 0, 1099), -1).` sets up a transfer, which pairs an account with a signed integer. In this case, the account is your account and the amount is -1. The negative number indicates that the balance of your account will be decremented by this amount.

- Line __5__: `Transfer(hedera.NewAccountID(0, 0, 1100), 1).` creates a second transfer, pairing an account with a signed integer. In this case, the account is your friend's account and the amount is 1. The positive number indicates that the balance of your account will be incremented by this amount. __Important__: the __sum of all transfers__ contained within in a `CryptoTransfer` __must equal zero__.

- Lines __6__ and __7__: `Sign(operatorSecret).` adds a signature based on a secret key. It is necessary to repeat this line to sign as both operator initiating the transfer transaction and account holder associated with an outgoing (negative) transfer – even though both keys are the same.

- Line __8__: `Execute()` executes the transaction.

  Next, the ID of the transaction itself is captured from the `response` in the above statement. The `transactionID` is made up of the account ID and the transaction timestamp right down to nanoseconds.

```go
  transactionID := response.ID

  time.Sleep(1 * time.Second)
```

  You can now request a `receipt` and print the status using the following code. Although this is not a mandatory step, it does verify that your transaction successfully reached network consensus.

```go
  receipt, err := client.GetTransactionReceipt(transactionID).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Transfer Transaction Status: %v \n", receipt.Status)

  time.Sleep(1 * time.Second)
```

  A status code of __1__ indicates success.

  Finally, you can requery the balance of both accounts to verify that 1 _hbar_ was indeed transferred from your account to that of your friend.

```go
  myBalance, err = client.GetAccountBalance(myAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Your new balance: %v \n", myBalance)

  time.Sleep(1 * time.Second)

  friendBalance, err = client.GetAccountBalance(friendAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Friend new balance: %v \n", friendBalance)
```

- Run the program again by executing `go run main.go` from terminal.

- If neither account has made any transfers previously, you should see `Your new balance; 9999` followed by `Friend new balance; 10001` demonstarting that 1 _hbar_ has been transferred from your account to you friend's account.

#### Hackathon-specific testnet configuration

- Transactions are throttled to one per second
  - Fee schedule disabled, so transactions will incur no fees.
  - Very early access to Hedera.
  - Virtual infrastructure supporting testnets.
  - Crypto Transfers will be throttled to 100/s if no receipt or record is requested.

- Only ED25519 keys are supported
  - ECDSA and RSA not supported yet, but "watch this space."

- It's unlikely, but your testnet may be rebooted
  - It's possible that your state may be erased. We will email you if that happens.
  - Please don’t create too many entities (< 1000) or use too much storage (< 1GB)

- We want to encourage innovation – not stress-testing of the testnets

- System logs will be analyzed after the event.
  - Prizes in __ℏ__ may be awarded to those demonstrating paticularly imaginative use of the SDKs.

#### API and SDK Overview

The Hedera API is based on [Google Protobuf](https://developers.google.com/protocol-buffers/), which supports code generation and is highly optimised. The transport layer is currently gRPC. Hedera is seeding several open-source SDKs under Apache 2.0.

##### Currently Available SDKs

- Currently supported for Micropay:
  - :boom: [Hedera Rust SDK](https://github.com/hashgraph/hedera-sdk-rust)
  - :boom: [Hedera C SDK](https://github.com/hashgraph/hedera-sdk-c)
  - :boom: [Hedera Go SDK](https://github.com/hashgraph/hedera-sdk-go)
- Coming soon:
  - Hedera Python SDK
  - Hedera node.js SDK

At Hedera, we would like to encourage the community to build more SDKs

##### SDK Functionality

- Abstraction of protobuf complexity
- OOTB support for cryptographic keys
- Easy on-ramp for app developers


### Questions and Answers

Do you have a development question for the Hedera team? Do you feel confident answering developer questions?

[Hedera Q & A](https://hashgraph.org/categories/hedera-q-a) is your space to ask any technical questions or participate in Q and A about development on the Hedera platform.


## What is the **Hedera** Hashgraph platform?

The Hedera hashgraph platform provides a new form of distributed consensus; a way for people who don't know or trust each other to securely collaborate and transact online without the need for a trusted intermediary. The platform is lightning fast, fair, and secure and, unlike some blockchain-based platforms, doesn’t require compute-heavy proof-of-work. Hedera enables and empowers developers to build an entirely new class of decentralized applications that were never before possible.

### Fast

Hedera hashgraph is fast. Right at the speed of your internet fast. The platform is built on the virtual-voting consensus algorithm, invented by Dr. Leemon Baird. This algorithm provides near-perfect efficiency in bandwidth usage, handling hundreds of thousands of micro-payment transactions per second and verifying over one million signatures per second. Time to finality is measured in seconds; not minutes, hours, or days. Consensus is 100% certain and, unique to Hedera, guaranteed to never change.

### Fair

Hedera hashgraph is fair, ensuring the consensus order of transactions reflects the transaction order received by the community. The platform ensures no single user can block the flow of transactions into the community, and no small group of users can unduly influence the consensus order of these transactions. These features are absent from many distributed ledger technologies, but are a requirement for existing applications today, such as markets and games.

### Secure

Hedera hashgraph has the strongest level of security possible in this category, which is Asynchronous Byzantine fault tolerance (ABFT). The platform is the only distributed ledger technology that has formally proven this quality. Achieving this level of security at scale is a fundamental advance in the field of distributed systems. Hedera guarantees consensus, in real time, and is resistant to Distributed Denial of Service (DDoS) attacks, an area of vulnerability for some public ledger platforms.

### Trustworthy

With Hedera hashgraph there are no leaders; everyone gets a vote. Platform-level trust is achieved by explicitly _mistrusting_ each individual node, but requiring 2/3 or more of tokens held by (and proxied to) all nodes to determine each and every vote.

## Other resources

- For an explanation of the underlying hashgraph algorithm, please consult our [whitepaper](https://www.hedera.com/hh-whitepaper-v1.4-181017.pdf) or Dr. Leemon Baird's 52-minute [Simple Explanation](https://www.youtube.com/watch?v=wgwYU1Zr9Tg) video.
- Hedera news can be found in the [Hedera Blog](https://www.hedera.com/blog) including recent Coq validation of the hashgraph ABFT algorithm.
- 250+ [Hedera interviews and videos](https://www.youtube.com/watch?v=v2M0eo9PRxw&list=PLuVX2ncHNKCwe1BdF6GH6RnjrF7J7yTZ4) on YouTube. Thanks to Arvyda – a Hedera MVP – for curating this list.

### Getting in touch

Please reach out to us on the Hedera [discord channels](https://hedera.com/discord). We're fortunate to have an active community of over 5000 like-minded devs, who are passionate about our tech. The Dev Advocacy team also participates actively.[https://hedera.com](https://cdn.frontify.com/api/screen/thumbnail/eYJA2myblmInvdfPogN-Bk6PpLDYBMJfo_wUyU8AjLzM-PigLcgvyVV39Qt96LheiBJwbDiSgFu3Q2ci3qT2IA/1360)

# Getting Started with Hedera 

### Getting connected through the [Hedera portal](https://go.hedera.com)

#### ID Verification

We want to allow devs to earn __ℏ__ by using our APIs. In order to be allowed to do this under US law we need to verify your identity on the [Hedera Portal](https://go.hedera.com). This process is explained in detail in [this video](https://youtu.be/1pJRNOde9Vw).

_Should the automated identity verification fail, please email compliance@hedera.com with your name and email used to create your account._

#### Getting access to a Hedera testnet

For illustrative purposes, the examples below use the Hedera Go SDK. You can use whichever of the Hedera SDKs you prefer. If you prefer, you can watch a [video walkthrough](https://youtu.be/0O0-Vie6v5U) of these steps to get you connected and make your first micro-payment.

##### 1. Create a Hedera account

- Complete the ID verification process (see above)

##### 2. Enter your testnet access code to your Hedera Account

- Testnet access codes are provided at Meetups and hackathon events. If you do not have a testnet access code you can register your interest via a link in the Hedera portal.eted registration.

##### 3. Get your environment configured

- Create a folder for your repo. In terminal: `mkdir hedera-z2m` followed my `cd hedera-z2m`
- So that you don't have to build your entire codebase from scratch make sure you have git-lfs installed. In terminal: `brew install git-lfs`
- Initialise a new module in Go. In terminal `go mod init github.com/<username>/hedera-z2m` making sure that you replace `<username>` with your own github username.
- Use your IDE of choice to manipulate source code in subsequent steps. In the Hedera DA team both [VSCode](https://code.visualstudio.com/docs/languages/go) and [GoLand](https://www.jetbrains.com/go/) are commonly used.

##### 4. Create your public/private keypair

- You can achieve this easily with the following go code (see file `keys.go` attached to this gist)

```go
package main

import (
  "fmt"

  "github.com/hashgraph/hedera-sdk-go"
)

func main() {
  secret := hedera.GenerateSecretKey()
  fmt.Printf("secret = %v\n", secret)

  public := secret.Public()
  fmt.Printf("public = %v\n", public)
}
```

- Execute this code from terminal, using `go run keys.go`
- Make a note of both of the keys output generated. For a testnet you can copy and paste the keys into a text file, although for security reasons you should ___never do this for mainnet___.

##### 5. Paste your _public_ key into the Hedera portal to complete the testnet registration process

- There are several key items shown in the Hedera portal. Keep the Hedera portal open or make a node of these items so that you can connect to the testnet:
  - Your Hedera __Account ID__ for this testnet – e.g. `0:0:1099`
  - The __testnet Address__ and __Port__ – e.g. `testnet.hedera.com:50123`
  - The Hedera __Node ID__ – e.g. `0:0:3`

  All Hedera IDs consist of three long-integers separated by colons. The three numbers represent `Shard-number`, `Realm number` and `Account number` respectively. Shards and Realms are not yet in use so expect the first two numbers to be zeros.

##### 6. Your first Hedera application – Check your account balance

All of the code explained from here to the end of Step 9 is contained within the file `main.go` attached to this gist)

- Create a new `main.go` file as follows:

```go
package main

import (
  "fmt"
  "time"

  "github.com/hashgraph/hedera-sdk-go"
)

func main() {
```

  Establish connection to the Hedera node by using the __testnet Address__ and __Port__ shown in the Hedera portal. Be sure to replace the example `50123` to your specific port.

  Defer the disconnection of the connection to guarantee a clean disconnect from the node.

```go
  client := hedera.Dial("testnet.hedera.com:50123")
  defer client.Close()
```

  Initialise the `myAccount` variable based on your __Account ID__ from the portal. Ensure that you replace the example `1099` with your own Account ID.

```go
  myAccount := hedera.NewAccountID(0, 0, 1099)
```

  Check your account balance. `GetAccountBalance` constructs the request; adding `.Answer()` executes the request. Don't forget error-handling.

  `fmt.Printf` can then output the balance.

```go
  myBalance, err := client.GetAccountBalance(myAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Your balance: %v \n", myBalance)
```

  Finally, close the braces for `func main`.

```go
}
```

- You should now be able to run your first Hedera program by executing `go run main.go` from terminal.

- If everything goes according to plan you should see `Your balance; 10000` which represents the initial number of _hbars_ in your testnet account.

##### 7. A note on testnet throttling

- For hackathon purposes, testnets have been throttled, allowing a limited number of Hedera transactions per account per second. Hackathon-specific testnet configuration is further described in a section later in this document.

- In order to accommodate testnet throttling, it's necessary to add a short delay between transactions issued to the Hedera node. To add a one second delay, use the following code:

```go
  time.Sleep(1 * time.Second)
```

- If such delays are not included between transactions, it is likely that `transaction failed the pre-check: Busy` errors will be observed upon execution.

##### 8. Improve your application – check your friend's account balance

- If you know the account ID of another account on your testnet – perhaps a friend or colleague – you can also check their balance. If your friends won’t share their accounts, or if you don’t have any friends, see the `account.go` file attached to this gist in order to create additional accounts.

- For the purposes of this example, an Account ID of `0:0:1100` will be used for that second account. Don't forget to amend `1100` to the account number of your friend's account. Failing to do this will likely result in a `transaction failed the pre-check: InvalidAccount` message.

- To continue with the example, add the following code into `func main` before the closing braces:

  Before executing any transfers, you can initialise a second variable `friendAccount` representing the second account, query its balance and output the result.

```go
  friendAccount := hedera.NewAccountID(0, 0, 1100)

  friendBalance, err = client.GetAccountBalance(friendAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Friend balance: %v \n", friendBalance)
```

  Once again, a delay is be added to accommodate testnet throttling. For brevity, this statement will be included _without further comment_ in all subsequent examples.

```go
  time.Sleep(1 * time.Second)
```

- Run the program again by executing `go run main.go` from terminal.

- Assuming that neither account has made any transfers so far, you should see `Your balance; 10000` followed by `Friend balance; 10000` as the initial number of _hbars_ in both testnet account is the same.

##### 9. Extend your application – transfer _hbars_ from your account to your friend's account

- Your __secret__ key (also known as _private_ key) is required in order to transfer _hbars_ out of your account. You should have noted this when it was generated in Step 4 of this process (above).

- The term "operator" used in the naming of the next variable `operatorSecret` is used to highlight the fact that this is the account responsible for submitting the transaction. Ensure that your replace `<my-secret-key>` with your own secret key in the following code block:

```go
  operatorSecret, err := hedera.SecretKeyFromString("<my-secret-key>")
  if err != nil {
    panic(err)
  }
```

  The next statement is more complex as it takes advantage of the builder pattern. The statement is included in its entirety; each line is explained individually below. Take care to replace `1099` with your account number and `1100` with your friend's account number.

```go
  response, err := client.CryptoTransfer().
    Operator(hedera.NewAccountID(0, 0, 1099)).
    Node(hedera.NewAccountID(0, 0, 3)).
    Transfer(hedera.NewAccountID(0, 0, 1099), -1).
    Transfer(hedera.NewAccountID(0, 0, 1100), 1).
    Sign(operatorSecret).
    Sign(operatorSecret).
    Execute()
    if err != nil {
      panic(err)
    }
```

- Line __1__: `response, err := client.CryptoTransfer().` creates a transaction to transfer _hbars_ between accounts.

- Line __2__: `Operator(hedera.NewAccountID(0, 0, 1099)).` identifies the account initiating the transaction.

- Line __3__: `Node(hedera.NewAccountID(0, 0, 3)).` identifies the account of the Hedea node to which the transaction is being sent.

- Line __4__: `Transfer(hedera.NewAccountID(0, 0, 1099), -1).` sets up a transfer, which pairs an account with a signed integer. In this case, the account is your account and the amount is -1. The negative number indicates that the balance of your account will be decremented by this amount.

- Line __5__: `Transfer(hedera.NewAccountID(0, 0, 1100), 1).` creates a second transfer, pairing an account with a signed integer. In this case, the account is your friend's account and the amount is 1. The positive number indicates that the balance of your account will be incremented by this amount. __Important__: the __sum of all transfers__ contained within in a `CryptoTransfer` __must equal zero__.

- Lines __6__ and __7__: `Sign(operatorSecret).` adds a signature based on a secret key. It is necessary to repeat this line to sign as both operator initiating the transfer transaction and account holder associated with an outgoing (negative) transfer – even though both keys are the same.

- Line __8__: `Execute()` executes the transaction.

  Next, the ID of the transaction itself is captured from the `response` in the above statement. The `transactionID` is made up of the account ID and the transaction timestamp right down to nanoseconds.

```go
  transactionID := response.ID

  time.Sleep(1 * time.Second)
```

  You can now request a `receipt` and print the status using the following code. Although this is not a mandatory step, it does verify that your transaction successfully reached network consensus.

```go
  receipt, err := client.GetTransactionReceipt(transactionID).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Transfer Transaction Status: %v \n", receipt.Status)

  time.Sleep(1 * time.Second)
```

  A status code of __1__ indicates success.

  Finally, you can requery the balance of both accounts to verify that 1 _hbar_ was indeed transferred from your account to that of your friend.

```go
  myBalance, err = client.GetAccountBalance(myAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Your new balance: %v \n", myBalance)

  time.Sleep(1 * time.Second)

  friendBalance, err = client.GetAccountBalance(friendAccount).Answer()
  if err != nil {
    panic(err)
  }

  fmt.Printf("Friend new balance: %v \n", friendBalance)
```

- Run the program again by executing `go run main.go` from terminal.

- If neither account has made any transfers previously, you should see `Your new balance; 9999` followed by `Friend new balance; 10001` demonstarting that 1 _hbar_ has been transferred from your account to you friend's account.

#### Hackathon-specific testnet configuration

- Transactions are throttled to one per second
  - Fee schedule disabled, so transactions will incur no fees.
  - Very early access to Hedera.
  - Virtual infrastructure supporting testnets.
  - Crypto Transfers will be throttled to 100/s if no receipt or record is requested.

- Only ED25519 keys are supported
  - ECDSA and RSA not supported yet, but "watch this space."

- It's unlikely, but your testnet may be rebooted
  - It's possible that your state may be erased. We will email you if that happens.
  - Please don’t create too many entities (< 1000) or use too much storage (< 1GB)

- We want to encourage innovation – not stress-testing of the testnets

- System logs will be analyzed after the event.
  - Prizes in __ℏ__ may be awarded to those demonstrating paticularly imaginative use of the SDKs.

#### API and SDK Overview

The Hedera API is based on [Google Protobuf](https://developers.google.com/protocol-buffers/), which supports code generation and is highly optimised. The transport layer is currently gRPC. Hedera is seeding several open-source SDKs under Apache 2.0.

##### Currently Available SDKs

- Currently supported for Micropay:
  - :boom: [Hedera Rust SDK](https://github.com/hashgraph/hedera-sdk-rust)
  - :boom: [Hedera C SDK](https://github.com/hashgraph/hedera-sdk-c)
  - :boom: [Hedera Go SDK](https://github.com/hashgraph/hedera-sdk-go)
- Coming soon:
  - Hedera Python SDK
  - Hedera node.js SDK

At Hedera, we would like to encourage the community to build more SDKs

##### SDK Functionality

- Abstraction of protobuf complexity
- OOTB support for cryptographic keys
- Easy on-ramp for app developers


### Questions and Answers

Do you have a development question for the Hedera team? Do you feel confident answering developer questions?

[Hedera Q & A](https://hashgraph.org/categories/hedera-q-a) is your space to ask any technical questions or participate in Q and A about development on the Hedera platform.


## What is the **Hedera** Hashgraph platform?

The Hedera hashgraph platform provides a new form of distributed consensus; a way for people who don't know or trust each other to securely collaborate and transact online without the need for a trusted intermediary. The platform is lightning fast, fair, and secure and, unlike some blockchain-based platforms, doesn’t require compute-heavy proof-of-work. Hedera enables and empowers developers to build an entirely new class of decentralized applications that were never before possible.

### Fast

Hedera hashgraph is fast. Right at the speed of your internet fast. The platform is built on the virtual-voting consensus algorithm, invented by Dr. Leemon Baird. This algorithm provides near-perfect efficiency in bandwidth usage, handling hundreds of thousands of micro-payment transactions per second and verifying over one million signatures per second. Time to finality is measured in seconds; not minutes, hours, or days. Consensus is 100% certain and, unique to Hedera, guaranteed to never change.

### Fair

Hedera hashgraph is fair, ensuring the consensus order of transactions reflects the transaction order received by the community. The platform ensures no single user can block the flow of transactions into the community, and no small group of users can unduly influence the consensus order of these transactions. These features are absent from many distributed ledger technologies, but are a requirement for existing applications today, such as markets and games.

### Secure

Hedera hashgraph has the strongest level of security possible in this category, which is Asynchronous Byzantine fault tolerance (ABFT). The platform is the only distributed ledger technology that has formally proven this quality. Achieving this level of security at scale is a fundamental advance in the field of distributed systems. Hedera guarantees consensus, in real time, and is resistant to Distributed Denial of Service (DDoS) attacks, an area of vulnerability for some public ledger platforms.

### Trustworthy

With Hedera hashgraph there are no leaders; everyone gets a vote. Platform-level trust is achieved by explicitly _mistrusting_ each individual node, but requiring 2/3 or more of tokens held by (and proxied to) all nodes to determine each and every vote.

## Other resources

- For an explanation of the underlying hashgraph algorithm, please consult our [whitepaper](https://www.hedera.com/hh-whitepaper-v1.4-181017.pdf) or Dr. Leemon Baird's 52-minute [Simple Explanation](https://www.youtube.com/watch?v=wgwYU1Zr9Tg) video.
- Hedera news can be found in the [Hedera Blog](https://www.hedera.com/blog) including recent Coq validation of the hashgraph ABFT algorithm.
- 250+ [Hedera interviews and videos](https://www.youtube.com/watch?v=v2M0eo9PRxw&list=PLuVX2ncHNKCwe1BdF6GH6RnjrF7J7yTZ4) on YouTube. Thanks to Arvyda – a Hedera MVP – for curating this list.

### Getting in touch

Please reach out to us on the Hedera [discord channels](https://hedera.com/discord). We're fortunate to have an active community of over 5000 like-minded devs, who are passionate about our tech. The Dev Advocacy team also participates actively.
