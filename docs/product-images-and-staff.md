# Product images and Staff accounts

## Product image behavior

Product forms accept drag-and-drop or file selection for JPEG, PNG, and WebP images up to 6 MB. The server verifies the image, strips metadata, applies orientation, resizes large images, and stores a WebP copy with a random name. Admins and Staff can also enter an HTTPS image URL; uploaded files replace that URL when both are supplied. The database continues to use `products.image_url` to store the resulting local path or canonical S3 object URL, so no schema migration is needed.

Development defaults to `UPLOAD_STORAGE=local`; Docker Compose keeps uploaded files in the `uploads_data` named volume. Production defaults to private S3 storage. Set these non-secret environment values in the production env file:

```dotenv
UPLOAD_STORAGE=s3
S3_BUCKET=your-private-bucket-name
AWS_REGION=ap-southeast-2
```

Keep S3 Block Public Access enabled. The app does not set public ACLs: it stores a stable object URL in MySQL and signs short-lived read URLs when an image is displayed. On EC2, grant the application only `s3:PutObject`, `s3:GetObject`, and `s3:DeleteObject` on `arn:aws:s3:::your-private-bucket-name/products/*`, preferably through an EC2 instance profile. Do not put AWS access keys in the app env file or source code. Uploading in production reports a configuration error until the bucket is configured and the instance has those permissions; the rest of the site can start without them.

## Staff accounts

Only Admin can visit `/admin/staff`, create Staff accounts, and activate or deactivate them. The role is assigned server-side as `staff`; the form never accepts a role. Staff can sign in to the existing business workspace but server-side `admin_required` routes, including `/admin` and `/admin/staff`, remain restricted to Admin. Deactivation prevents another authenticated request from loading that account.

New Staff users use the existing `users` table and roles constraint, so this feature adds no database migration. Admin supplies the initial password (minimum 12 characters) and must share it with the staff member through a secure channel.
