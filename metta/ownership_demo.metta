(= (collective-owner $artwork $collective)
   (match &self (, (owner-of $artwork $person) (member-of $person $collective)) $collective))
