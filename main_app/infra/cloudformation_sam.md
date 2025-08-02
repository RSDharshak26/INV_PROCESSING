aws cloudformation deploy --template-file infra.yml --stack-name my-app-infra --capabilities CAPABILITY_NAMED_IAM --region us-east-1

# Delete the failed stack from yesterday
aws cloudformation delete-stack --stack-name my-app-infra --region us-east-1


 Wait for deletion to complete (this might take a few minutes)
aws cloudformation wait stack-delete-complete --stack-name my-app-infra --region us-east-1


sam build --use_container

sam deploy --guided 


#get url of lambda function 
