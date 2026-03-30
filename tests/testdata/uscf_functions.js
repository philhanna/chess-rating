var isDual;


function check()
  {
  isDual = "N";
  if (document.getElementById('DUALK').checked)
     isDual = "Y";
  }


function computeBonus( score, myExp, myK, myCurrentGames )
{
	var myConstant = 10;
	var myBonusGameCount;

	if ( myCurrentGames < 4 )
		myBonusGameCount = 4;
	else
		myBonusGameCount = myCurrentGames;

	var myBonus;
	myBonus = myK * ( score - myExp ) - myConstant * Math.sqrt( myBonusGameCount );
	if ( myBonus < 0 )
		myBonus = 0;
	if ( myCurrentGames < 3 )
		myBonus = 0;
	return myBonus;
}

function computeK( oldRating, myGameCount, myCurrentGames, DualK )
{
	var myPriorGames;
	var myK;

	if (oldRating < 2355)
		myPriorGames = 50.0 / Math.sqrt( 0.662 + (2569-oldRating )*(2569-oldRating)*0.000007390);
	else
		myPriorGames = 50;

	if ( myPriorGames > myGameCount )
		myPriorGames = myGameCount;

	myK = 800.0 / ( myPriorGames + myCurrentGames );

        if (isDual == "Y") 
        {
           if (oldRating < 2200) 
              myK = myK;
           else if (oldRating >= 2500)
              myK = myK / 4.0;
           else 
              myK = (6.5 - 0.0025*oldRating)* myK;
        }

	return myK;
}

function performanceRating( Established, fScore, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12 )
{
	var jj, myExp=0., pvEst = 0., myEst=4000., myLow=0., myHigh=4000., fDiff=0., iRating=0;
	var bEstablished, iCount = 0;
	var log10;
	log10 = Math.log( 10 );
	var ratingDiff;
	var TRUE = -1;
	var FALSE = 0;
	var totalRating=0;

	for (jj=2; jj<performanceRating.length; jj++)
	{
		if( performanceRating.arguments[jj] != "" )
		{
			iCount++;
			iRating = parseInt( performanceRating.arguments[jj] );
			totalRating += iRating;
		}
	}

	bEstablished = Established;
	if ( bEstablished == TRUE )
		if (Math.abs( fScore ) < .001 || Math.abs( iCount - fScore ) < .001)
			bEstablished = FALSE;

	while( Math.abs( myEst - pvEst ) > .1 )
	{
		myExp = 0.;

		for (jj=2; jj<performanceRating.length; jj++)
		{
			if( performanceRating.arguments[jj] != "" )
			{
				iRating = parseInt( performanceRating.arguments[jj] );
				if ( bEstablished == FALSE )
				{
					ratingDiff = myEst - iRating;
					if ( ratingDiff > 400 )
						myExp += 1.;
					else if ( ratingDiff < -400 )
						myExp += 0.;
					else
						myExp += 0.5 + ratingDiff/800;
				}
				else
					myExp += 1./(Math.exp(log10*((iRating-myEst)/400.))+1.);
			}
		}

		fDiff = myExp - fScore;
		pvEst = myEst;
		if ( fDiff > 0. )
		{
			myHigh = myEst;
			myEst = ( myEst + myLow ) / 2.;
		}
		else
		{
			myLow = myEst;
			myEst = ( myEst + myHigh ) / 2.;
		}
	}

	if ( bEstablished == FALSE )
		if ( Math.abs( fScore ) < .001 )
		{
			myEst = 4000;
			for (jj=2; jj<performanceRating.length; jj++)
				if ( performanceRating.arguments[jj] != "" )
				{
					iRating = parseInt( performanceRating.arguments[jj] );
					if ( iRating < myEst )
						myEst = iRating;
				}
			myEst = Math.max( 100, myEst-400 );
		}
		else if ( Math.abs( iCount - fScore ) < .001 )
		{
			myEst = 0;
			for (jj=2; jj<performanceRating.length; jj++)
				if ( performanceRating.arguments[jj] != "" )
				{
					iRating = parseInt( performanceRating.arguments[jj] );
					if ( iRating > myEst )
						myEst = iRating;
				}
			myEst = Math.min( 2700, myEst+400);
		}

	return Math.round( myEst );
}

function newRating( GameCount, myOldRating, DualK, score, age, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12 )
{

	var myGameCount = parseInt( GameCount );
	var oldRating;
	var roundAway;

	if ( myGameCount > 0 )
	{
		if ( myOldRating == "" )
			return "";
		oldRating = parseInt( myOldRating );
	}
	else
	{
		if ( myOldRating == "" )
			if ( age == "" )
				oldRating = 750;
			else
				oldRating = 300 + 50. * Math.max( Math.min( age, 20 ), 4);
		else
			oldRating = parseInt( myOldRating );
	}

	var jj, myExp=0., iRating=0; iCount=0;
	var log10;
	var myCurrentGames=0;
	log10 = Math.log( 10 );
	var sumRatings=0;

	for (jj=5; jj<newRating.length; jj++)
	{
		if( newRating.arguments[jj] != "" )
		{
			myCurrentGames++;
			iRating = parseInt( newRating.arguments[jj] );
			myExp += 1./(Math.exp(log10*((iRating-oldRating)/400.))+1.);
			sumRatings += iRating;
			iCount++;
		}
	}

	if ( myGameCount <= 8 )
	{
		var FALSE = 0;
		rating = performanceRating( FALSE, score,
			r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12 );
		if ( myGameCount == 0 &&
			( score == 0 && oldRating < rating || score == iCount && oldRating > rating ))
			rating = oldRating;
		else
			rating = ( myGameCount * oldRating + myCurrentGames * rating ) /
				( myGameCount + myCurrentGames );
		roundAway = 0.0;
	}
	else
	{
		var myK;
		var myBonus;
		myK = computeK( oldRating, myGameCount, myCurrentGames, DualK);
		myBonus = computeBonus( score, myExp, myK, myCurrentGames );
		rating = oldRating + myK * ( score - myExp ) + myBonus;
		if ( oldRating < rating )
			roundAway = .4999;
		else
			roundAway = -.4999;
	}
	return Math.round( rating + roundAway );
}

function getK( GameCount, myOldRating, DualK, score, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12)
{
	if ( myOldRating == "" ) return "";

	var oldRating = parseInt( myOldRating );
	var myGameCount = parseInt( GameCount );
	if ( myGameCount <= 8 )
		return ("N/A");

	var jj;
	var myCurrentGames=0;

	for (jj=4; jj<getK.length; jj++)
	{
		if( getK.arguments[jj] != "" )
		{
			myCurrentGames++;
		}
	}

	var myK;

	myK = computeK( oldRating, myGameCount, myCurrentGames, DualK);

	return Math.round(100*myK)/100;
}

function getBonus( GameCount, myOldRating, DualK, score, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12 )
{
	if ( myOldRating == "" ) return "";

	var oldRating = parseInt( myOldRating );
	var myGameCount = parseInt( GameCount );
	if ( myGameCount <= 8 )
		return ("N/A");

	var jj, myExp=0., iRating=0;
	var log10;
	var myCurrentGames=0;
	log10 = Math.log( 10 );

	for (jj=4; jj<getBonus.length; jj++)
	{
		if( getBonus.arguments[jj] != "" )
		{
			myCurrentGames++;
			iRating = parseInt( getBonus.arguments[jj] );
			myExp += 1./(Math.exp(log10*((iRating-oldRating)/400.))+1.);
		}
	}

	if ( myCurrentGames < 3 )
		return ("N/A");

	var myK;
	var myBonus;

	myK = computeK( oldRating, myGameCount, myCurrentGames, DualK );

	myBonus = computeBonus( score, myExp, myK, myCurrentGames );

	return Math.round(100*myBonus)/100;
}
