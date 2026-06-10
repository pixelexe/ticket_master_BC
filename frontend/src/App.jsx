/* eslint-disable react-hooks/preserve-manual-memoization, react-hooks/set-state-in-effect */
import { useCallback, useEffect, useState } from 'react'
import { BrowserProvider, Contract, formatEther } from 'ethers'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || '/api'
const SEPOLIA_CHAIN_ID = 11155111n
const IPFS_GATEWAY = 'https://gateway.pinata.cloud/ipfs/'

const CONTRACT_ABI = [
  'function buy(uint256 quantity) payable returns (uint256[])',
  'function price() view returns (uint256)',
  'function remainingSupply() view returns (uint256)',
  'function balanceOf(address owner) view returns (uint256)',
  'function ownerOf(uint256 tokenId) view returns (address)',
  'function tokenURI(uint256 tokenId) view returns (string)',
  'function ticketsOf(address account) view returns (uint256[])',
  'function withdraw()',
]

function shortAddress(address) {
  return address ? `${address.slice(0, 6)}...${address.slice(-4)}` : ''
}

function getEthereum() {
  return window.ethereum
}

function ipfsToHttp(uri) {
  return uri?.startsWith('ipfs://')
    ? `${IPFS_GATEWAY}${uri.slice('ipfs://'.length)}`
    : uri
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds))
}

function App() {
  const [events, setEvents] = useState([])
  const [sellerAddress, setSellerAddress] = useState('')
  const [selectedEventId, setSelectedEventId] = useState('')
  const [categories, setCategories] = useState([])
  const [selectedCategoryId, setSelectedCategoryId] = useState('')
  const [hasMetaMask] = useState(() => Boolean(getEthereum()?.isMetaMask))
  const [account, setAccount] = useState('')
  const [walletBalance, setWalletBalance] = useState(null)
  const [chainId, setChainId] = useState(null)
  const [price, setPrice] = useState(null)
  const [remaining, setRemaining] = useState(null)
  const [contractBalance, setContractBalance] = useState(null)
  const [ownedTickets, setOwnedTickets] = useState(null)
  const [tickets, setTickets] = useState([])
  const [isLoadingTickets, setIsLoadingTickets] = useState(false)
  const [status, setStatus] = useState('')
  const [isBusy, setIsBusy] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState('wallet')
  const [cardNumber, setCardNumber] = useState('4242424242424242')
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    starts_at: '',
  })
  const [categoryForm, setCategoryForm] = useState({
    title: '',
    description: '',
    price_wei: '10000000000000000',
    max_supply: '100',
    image: null,
  })

  const selectedEvent = events.find(
    (event) => event.id === Number(selectedEventId),
  )
  const selectedCategory = categories.find(
    (category) => category.id === Number(selectedCategoryId),
  )
  const contractAddress = selectedCategory?.contract_address ?? ''
  const isSeller = Boolean(
    account &&
      sellerAddress &&
      account.toLowerCase() === sellerAddress.toLowerCase(),
  )

  const loadPublicConfig = useCallback(async () => {
    const response = await fetch(`${API_URL}/config`)
    if (!response.ok) throw new Error('Unable to load application configuration')
    const config = await response.json()
    setSellerAddress(config.seller_address)
  }, [])

  const loadEvents = useCallback(async (preferredEventId) => {
    const response = await fetch(`${API_URL}/events`)
    if (!response.ok) throw new Error('Unable to load events')
    const loadedEvents = await response.json()
    setEvents(loadedEvents)

    if (preferredEventId) {
      setSelectedEventId(String(preferredEventId))
    } else if (loadedEvents.length) {
      setSelectedEventId((currentId) => {
        if (currentId) return currentId
        const defaultEvent =
          loadedEvents.find((event) => event.id === 3) ?? loadedEvents[0]
        return String(defaultEvent.id)
      })
    }
  }, [])

  const loadCategories = useCallback(async (eventId, preferredCategoryId) => {
    if (!eventId) {
      setCategories([])
      return
    }

    const response = await fetch(
      `${API_URL}/events/${eventId}/ticket-categories`,
    )
    if (!response.ok) throw new Error('Unable to load ticket categories')
    const loadedCategories = await response.json()
    setCategories(loadedCategories)

    const preferred = loadedCategories.find(
      (category) => category.id === Number(preferredCategoryId),
    )
    const defaultCategory =
      preferred ??
      loadedCategories.find((category) => category.contract_address) ??
      loadedCategories[0]
    setSelectedCategoryId(defaultCategory ? String(defaultCategory.id) : '')
  }, [])

  const loadContractData = useCallback(async (
    walletAddress = account,
    address = contractAddress,
  ) => {
    const ethereum = getEthereum()
    if (!ethereum || !address) {
      setTickets([])
      setOwnedTickets(null)
      return
    }

    const provider = new BrowserProvider(ethereum)
    const network = await provider.getNetwork()
    setChainId(network.chainId)
    if (network.chainId !== SEPOLIA_CHAIN_ID) return

    const contract = new Contract(address, CONTRACT_ABI, provider)
    const balancePromise = walletAddress
      ? provider.getBalance(walletAddress)
      : Promise.resolve(null)
    const [ticketPrice, ticketsLeft, balance, funds] = await Promise.all([
      contract.price(),
      contract.remainingSupply(),
      balancePromise,
      provider.getBalance(address),
    ])

    setPrice(ticketPrice)
    setRemaining(ticketsLeft)
    setWalletBalance(balance)
    setContractBalance(funds)

    if (!walletAddress) {
      setOwnedTickets(null)
      setTickets([])
      return
    }

    const ticketBalance = await contract.balanceOf(walletAddress)
    setOwnedTickets(ticketBalance)
    setIsLoadingTickets(true)

    try {
      const tokenIds = (await contract.ticketsOf(walletAddress)).map(
        (tokenId) => tokenId.toString(),
      )
      const loadedTickets = await Promise.all(
        tokenIds.map(async (tokenId) => {
          try {
            const owner = await contract.ownerOf(tokenId)
            if (owner.toLowerCase() !== walletAddress.toLowerCase()) return null
            const metadataUri = await contract.tokenURI(tokenId)
            const response = await fetch(ipfsToHttp(metadataUri))
            if (!response.ok) return null
            const metadata = await response.json()
            return {
              tokenId,
              name: metadata.name,
              description: metadata.description,
              image: ipfsToHttp(metadata.image),
            }
          } catch {
            return null
          }
        }),
      )
      setTickets(loadedTickets.filter(Boolean))
    } finally {
      setIsLoadingTickets(false)
    }
  }, [account, contractAddress])

  useEffect(() => {
    loadPublicConfig().catch((error) => setStatus(error.message))
  }, [loadPublicConfig])

  useEffect(() => {
    loadEvents().catch((error) => setStatus(error.message))
  }, [loadEvents])

  useEffect(() => {
    if (!selectedEventId) return
    loadCategories(selectedEventId).catch((error) => setStatus(error.message))
  }, [loadCategories, selectedEventId])

  useEffect(() => {
    if (!contractAddress) return
    loadContractData(account, contractAddress).catch((error) =>
      setStatus(error.shortMessage || error.message),
    )
  }, [account, contractAddress, loadContractData])

  useEffect(() => {
    const ethereum = getEthereum()
    if (!ethereum) return

    async function restoreWallet() {
      const accounts = await ethereum.request({ method: 'eth_accounts' })
      setAccount(accounts[0] ?? '')
    }
    function handleAccountsChanged(accounts) {
      setAccount(accounts[0] ?? '')
      setStatus('')
    }
    function handleChainChanged() {
      window.location.reload()
    }

    restoreWallet()
    ethereum.on('accountsChanged', handleAccountsChanged)
    ethereum.on('chainChanged', handleChainChanged)
    return () => {
      ethereum.removeListener('accountsChanged', handleAccountsChanged)
      ethereum.removeListener('chainChanged', handleChainChanged)
    }
  }, [])

  async function connectWallet() {
    if (!getEthereum()) {
      setStatus('MetaMask was not detected.')
      return
    }
    try {
      const accounts = await getEthereum().request({
        method: 'eth_requestAccounts',
      })
      setAccount(accounts[0])
      setStatus('')
    } catch (error) {
      setStatus(error.shortMessage || error.message)
    }
  }

  async function switchToSepolia() {
    try {
      await getEthereum().request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0xaa36a7' }],
      })
    } catch (error) {
      setStatus(error.message)
    }
  }

  async function buyTicket() {
    setIsBusy(true)
    setStatus('Confirm the transaction in MetaMask.')
    try {
      const provider = new BrowserProvider(getEthereum())
      const signer = await provider.getSigner()
      const contract = new Contract(contractAddress, CONTRACT_ABI, signer)
      const transaction = await contract.buy(1, { value: price })
      setStatus('Waiting for Sepolia confirmation...')
      await transaction.wait()
      setStatus('Ticket purchased successfully.')
      await loadContractData(account, contractAddress)
    } catch (error) {
      setStatus(
        error.code === 4001 || error.code === 'ACTION_REJECTED'
          ? 'Transaction cancelled in MetaMask.'
          : error.shortMessage || error.message,
      )
    } finally {
      setIsBusy(false)
    }
  }

  async function payByCard(event) {
    event.preventDefault()
    setIsBusy(true)
    setStatus('Simulating card payment and minting your NFT...')
    try {
      const response = await fetch(`${API_URL}/events/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category_id: selectedCategory.id,
          buyer_address: account,
          card_number: cardNumber.replaceAll(' ', ''),
        }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Card payment failed')
      setStatus(`Card payment accepted. Ticket #${result.token_id} minted.`)
      await wait(3000)
      await loadContractData(account, contractAddress)
    } catch (error) {
      setStatus(error.message)
    } finally {
      setIsBusy(false)
    }
  }

  async function withdrawFunds() {
    setIsBusy(true)
    setStatus('Confirm the withdrawal in MetaMask.')
    try {
      const provider = new BrowserProvider(getEthereum())
      const signer = await provider.getSigner()
      const contract = new Contract(contractAddress, CONTRACT_ABI, signer)
      const transaction = await contract.withdraw()
      await transaction.wait()
      setStatus('Contract funds withdrawn successfully.')
      await loadContractData(account, contractAddress)
    } catch (error) {
      setStatus(error.shortMessage || error.message)
    } finally {
      setIsBusy(false)
    }
  }

  async function createEvent(event) {
    event.preventDefault()
    setIsBusy(true)
    setStatus('Creating event...')
    try {
      const response = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...eventForm,
          starts_at: new Date(eventForm.starts_at).toISOString(),
        }),
      })
      const created = await response.json()
      if (!response.ok) throw new Error(created.detail || 'Event creation failed')
      setSelectedCategoryId('')
      setCategories([])
      await loadEvents(created.id)
      setEventForm({ title: '', description: '', starts_at: '' })
      setStatus(`Event "${created.title}" created. Add its ticket category.`)
    } catch (error) {
      setStatus(error.message)
    } finally {
      setIsBusy(false)
    }
  }

  async function createCategory(event) {
    event.preventDefault()
    if (!categoryForm.image) return
    setIsBusy(true)
    setStatus('Uploading to IPFS and deploying the NFT contract...')
    try {
      const formData = new FormData()
      formData.append('title', categoryForm.title)
      formData.append('description', categoryForm.description)
      formData.append('price_wei', categoryForm.price_wei)
      formData.append('max_supply', categoryForm.max_supply)
      formData.append('image', categoryForm.image)

      const response = await fetch(
        `${API_URL}/events/${selectedEventId}/ticket-categories`,
        { method: 'POST', body: formData },
      )
      const created = await response.json()
      if (!response.ok) {
        throw new Error(created.detail || 'Category creation failed')
      }
      await loadCategories(selectedEventId, created.id)
      setCategoryForm({
        title: '',
        description: '',
        price_wei: '10000000000000000',
        max_supply: '100',
        image: null,
      })
      setStatus(`Category "${created.title}" deployed successfully.`)
    } catch (error) {
      setStatus(error.message)
    } finally {
      setIsBusy(false)
    }
  }

  const isSepolia = chainId === SEPOLIA_CHAIN_ID
  const banner =
    ipfsToHttp(selectedEvent?.banner_ipfs_uri) ??
    ipfsToHttp(selectedCategory?.image_ipfs_uri)

  return (
    <>
      <header className="header">
        <a className="brand" href="/">
          <span className="brand-icon">T</span>
          TICKETING
        </a>
        <nav>
          <a href="#event">Events</a>
          <a href="#my-tickets">My tickets</a>
          {isSeller && <a href="#admin">Admin</a>}
        </nav>
        <button className="wallet-button" type="button" onClick={connectWallet}>
          {account ? (
            <>
              <span>{shortAddress(account)}</span>
              <small>
                {walletBalance === null
                  ? '...'
                  : `${Number(formatEther(walletBalance)).toFixed(4)} SepoliaETH`}
              </small>
            </>
          ) : hasMetaMask ? (
            'Connect MetaMask'
          ) : (
            'MetaMask not detected'
          )}
        </button>
      </header>

      <main>
        {status && <p className="status global-status">{status}</p>}

        <section className="selector-card">
          <label htmlFor="event-select">Event</label>
          <select
            id="event-select"
            value={selectedEventId}
            onChange={(event) => setSelectedEventId(event.target.value)}
          >
            {events.map((event) => (
              <option key={event.id} value={event.id}>
                {event.title}
              </option>
            ))}
          </select>
          <label htmlFor="category-select">Ticket category</label>
          <select
            id="category-select"
            value={selectedCategoryId}
            onChange={(event) => setSelectedCategoryId(event.target.value)}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.title}
              </option>
            ))}
          </select>
        </section>

        <section className="event" id="event">
          {banner && <img className="event-image" src={banner} alt="" />}
          <p className="eyebrow">
            {selectedEvent
              ? new Date(selectedEvent.starts_at).toLocaleString()
              : 'Select an event'}
          </p>
          <h1>{selectedEvent?.title ?? 'No event selected'}</h1>
          <p className="event-description">{selectedEvent?.description}</p>
        </section>

        {selectedCategory ? (
          <section className="ticket-card">
            <div className="ticket-heading">
              <div>
                <p className="eyebrow">TICKET CATEGORY</p>
                <h2>{selectedCategory.title}</h2>
              </div>
              <strong>
                {price === null ? '...' : `${formatEther(price)} ETH`}
              </strong>
            </div>
            <div className="ticket-details">
              <p>{selectedCategory.description}</p>
              <p>{remaining === null ? '...' : `${remaining} tickets left`}</p>
            </div>

            {!selectedCategory.contract_address && (
              <p className="notice">This category has no deployed contract.</p>
            )}
            {hasMetaMask && chainId !== null && !isSepolia && (
              <button className="primary-button" type="button" onClick={switchToSepolia}>
                Switch to Sepolia
              </button>
            )}
            {hasMetaMask && isSepolia && !account && (
              <button className="primary-button" type="button" onClick={connectWallet}>
                Connect MetaMask
              </button>
            )}
            {hasMetaMask && isSepolia && account && contractAddress && (
              <>
                <div className="payment-tabs">
                  <button
                    className={paymentMethod === 'wallet' ? 'active' : ''}
                    type="button"
                    onClick={() => setPaymentMethod('wallet')}
                  >
                    Pay with wallet
                  </button>
                  <button
                    className={paymentMethod === 'card' ? 'active' : ''}
                    type="button"
                    onClick={() => setPaymentMethod('card')}
                  >
                    Card payment
                  </button>
                </div>
                {paymentMethod === 'wallet' ? (
                  <button
                    className="primary-button"
                    type="button"
                    onClick={buyTicket}
                    disabled={isBusy || price === null || remaining === 0n}
                  >
                    Buy with MetaMask
                  </button>
                ) : (
                  <form className="card-form" onSubmit={payByCard}>
                    <label htmlFor="card-number">Fake card number</label>
                    <input
                      id="card-number"
                      value={cardNumber}
                      onChange={(event) => setCardNumber(event.target.value)}
                      minLength="12"
                      maxLength="19"
                      required
                    />
                    <button className="primary-button" type="submit" disabled={isBusy}>
                      Simulate card payment
                    </button>
                  </form>
                )}
              </>
            )}
            {status && <p className="status">{status}</p>}
          </section>
        ) : (
          <p className="notice">No ticket category for this event yet.</p>
        )}

        <section className="owned-card" id="my-tickets">
          <p className="eyebrow">MY TICKETS</p>
          <h2>
            {ownedTickets === null
              ? 'Connect your wallet'
              : `${ownedTickets} ${selectedCategory?.title ?? ''} ticket(s)`}
          </h2>
          {isLoadingTickets && <p>Loading your NFT tickets...</p>}
          <div className="ticket-list">
            {tickets.map((ticket) => (
              <article className="owned-ticket" key={ticket.tokenId}>
                <img src={ticket.image} alt={`${ticket.name} ticket`} />
                <div>
                  <p className="eyebrow">{selectedEvent?.title}</p>
                  <h3>{ticket.name}</h3>
                  <p>{ticket.description}</p>
                  <a
                    href={`https://sepolia.etherscan.io/nft/${contractAddress}/${ticket.tokenId}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Ticket #{ticket.tokenId} on Etherscan
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        {isSeller && (
          <section className="admin-card" id="admin">
            <p className="eyebrow">SELLER ADMIN</p>
            <h2>Create an event</h2>
            <form className="admin-form" onSubmit={createEvent}>
              <input
                placeholder="Title"
                value={eventForm.title}
                onChange={(event) =>
                  setEventForm({ ...eventForm, title: event.target.value })
                }
                required
              />
              <textarea
                placeholder="Description"
                value={eventForm.description}
                onChange={(event) =>
                  setEventForm({ ...eventForm, description: event.target.value })
                }
                required
              />
              <input
                type="datetime-local"
                value={eventForm.starts_at}
                onChange={(event) =>
                  setEventForm({ ...eventForm, starts_at: event.target.value })
                }
                required
              />
              <button className="primary-button" type="submit" disabled={isBusy}>
                Create event
              </button>
            </form>

            <h2>Create a category for {selectedEvent?.title}</h2>
            <form className="admin-form" onSubmit={createCategory}>
              <input
                placeholder="Category title"
                value={categoryForm.title}
                onChange={(event) =>
                  setCategoryForm({ ...categoryForm, title: event.target.value })
                }
                required
              />
              <textarea
                placeholder="Description"
                value={categoryForm.description}
                onChange={(event) =>
                  setCategoryForm({
                    ...categoryForm,
                    description: event.target.value,
                  })
                }
                required
              />
              <input
                type="number"
                placeholder="Price in wei"
                value={categoryForm.price_wei}
                onChange={(event) =>
                  setCategoryForm({
                    ...categoryForm,
                    price_wei: event.target.value,
                  })
                }
                min="1"
                required
              />
              <input
                type="number"
                placeholder="Maximum supply"
                value={categoryForm.max_supply}
                onChange={(event) =>
                  setCategoryForm({
                    ...categoryForm,
                    max_supply: event.target.value,
                  })
                }
                min="1"
                required
              />
              <input
                type="file"
                accept="image/*"
                onChange={(event) =>
                  setCategoryForm({
                    ...categoryForm,
                    image: event.target.files[0],
                  })
                }
                required
              />
              <button className="primary-button" type="submit" disabled={isBusy}>
                Upload to IPFS and deploy category
              </button>
            </form>

            {contractAddress && (
              <>
                <div className="admin-heading">
                  <div>
                    <h2>Contract revenue</h2>
                    <p>Funds received from on-chain ticket purchases.</p>
                  </div>
                  <strong>
                    {contractBalance === null
                      ? '...'
                      : `${formatEther(contractBalance)} ETH`}
                  </strong>
                </div>
                <button
                  className="primary-button"
                  type="button"
                  onClick={withdrawFunds}
                  disabled={
                    isBusy || contractBalance === null || contractBalance === 0n
                  }
                >
                  {contractBalance === 0n
                    ? 'No funds to withdraw'
                    : 'Withdraw to seller wallet'}
                </button>
              </>
            )}
            {status && <p className="status">{status}</p>}
          </section>
        )}
      </main>
    </>
  )
}

export default App
