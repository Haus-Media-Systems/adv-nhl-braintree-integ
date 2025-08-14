import braintree

# Configure Braintree sandbox
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id='cmw9qh963vbrbnp7',
        public_key='b4m63tfbnjh229qk',
        private_key='6dbee76c103a0c6bf6ae64a5076a9708'
    )
)
