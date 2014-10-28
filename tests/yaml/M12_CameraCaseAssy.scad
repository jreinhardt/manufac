// Un-official (China source) M12 mount 36 x 36 mm RPi-compatible camera
// (search "raspberry camera board M12x0.5 lens" on Ebay)
// Sept. 16, 2014  J. Beale
// version 1.1 (added 2mm to U-bracket to allow tilt motion with screw in place)

// ==============================================================
include <include.scad>;

module FlexCable() {
  color("grey") translate([0,-(CBL+FCL)/2+CBFCE,-FCZO]) 
	cube([FCW,FCL,FCH],center=true);
}

module M12Lens() {
  cylinder(r=LOD/2,h=LL,$fn=fn); // M12x.5 lens barrel
  translate([0,0,LL]) cylinder(r=LROD/2,h=LRH,$fn=fn); // rim of lens front objective
}

module CBoard() {
 difference() {
  union() {
   translate([-CBFCW/2,-(CBL/2 - CBFCE),-CBFCH]) 
		cube([CBFCW, CBFCL, CBFCH]); // 15-way flex conn
   translate([0,0,CBH/2]) cube([CBW,CBL,CBH],center=true); // PCB holding module
   translate([0,0,-CBBH/2]) color("grey") 
	cube([CBW-2*CBBS,CBL-2*CBBS,CBBH],center=true); // bottom keepout
   color("grey") translate([0,0,CBH+(CMH/2)]) 
		cube([CMW,CML,CMH],center=true); // base of camera module
   color("grey") translate([0,0,CBH+(CMH/2)]) cube([CMMW,CMML,CMH],center=true);
   color("grey") translate([0,0,CBH+(CMLH/2)]) cylinder(r=CMLOD/2,h=CMLH,center=true);
   color("grey") translate([-CMCW/2,0,CBH]) cube([CMCW,CMCTE-(CBL/2),CMCH]);
  }

  translate([0,0,eps]) cylinder(r=LOD/2,h=2*CMH,$fn=fn); // hole for M12 lens
  translate([(CBW-CBBCS)/2,(CBL-CBBCS)/2,-CBBH-eps]) 
	cube([CBBCS,CBBCS,CBBH*2],center=true); // bottom keepout area corner relief 
  translate([-(CBW-CBBCS)/2,(CBL-CBBCS)/2,-CBBH-eps]) 
	cube([CBBCS,CBBCS,CBBH*2],center=true); // bottom keepout area corner relief 
  translate([(CBW-CBBCS)/2,-(CBL-CBBCS)/2,-CBBH-eps]) 
	cube([CBBCS,CBBCS,CBBH*2],center=true); // bottom keepout area corner relief 
  translate([-(CBW-CBBCS)/2,-(CBL-CBBCS)/2,-CBBH-eps]) 
	cube([CBBCS,CBBCS,CBBH*2],center=true); // bottom keepout area corner relief 
  translate([MHCC/2,MHCC/2,-CBH*2]) 
		cylinder(r=MHOD/2,h=CBH*5,$fn=20); // 3mm mounting hole
  translate([MHCC/2,-MHCC/2,-CBH*2]) cylinder(r=MHOD/2,h=CBH*5,$fn=20);
  translate([-MHCC/2,MHCC/2,-CBH*2]) cylinder(r=MHOD/2,h=CBH*5,$fn=20);
  translate([-MHCC/2,-MHCC/2,-CBH*2]) cylinder(r=MHOD/2,h=CBH*5,$fn=20);
  // translate([0,0,-50]) cube([100,100,100]); // cutaway DEBUG
 } // end diff()
}

module CamAssy() { // model of M12 camera board
 CBoard();
 FlexCable();
 translate([0,0,5]) color("green") M12Lens();
}



// ===================================================
// == HOUSING for 36x36mm M12-lens camera board  ==

CCW = 40; // camera housing width (x axis)
CCL = 40; // camera housing length (y axis)
CCBD = 4; // camera housing back depth (z axis)
CCBF = 2.6; // camera housing back front lip height (z axis)
CCBIW = CBW+slop*2; // housing back interior width
CCBIL = CBL+slop*2; // housing back interior length
CCBSW = FCW+1; // width for flex cable slot
BS=8; // mounting screw boss width
BSO=0.8; // boss offset towards center

module CHB_outside() {
  difference() {
    union() {
    translate([-CCW/2,-CCL/2,-CCBD]) 
		cube([CCW,CCL,CCBD+CCBF]); // back body of housing
    }
    union() {
	  translate([-CCBSW/2,-(CCL/2)-eps,-1.6]) 
		cube([CCBSW,CCL/2,CCBD*2]); // slot for flex cable
      translate([-CCBIW/2,-CCBIL/2,-(CBFCH+slop)]) 
		cube([CCBIW,CCBIL,CCBD+CCBF]); // cutout hole for board
      // CamAssy();  // camera board assembly w/lens, flex cable
      // translate([+15,-100,-50]) cube([100,100,100]); // DEBUG cutaway

    }
  }
}

// =========================================================
// == Front part of camera housing

CCFH = 10.3; // height of camera case front part
CCFZoff = 2.6; // z-offset of camera case front
CCFT = 1.75; // thickness of camera case front
CCFB = 2.25;  // side hex boss height
CCFBOD = 14.42;  // side hex boss OD
CCFBID = 6.11+slop;  // side hex boss ID
CCFBZ = 5.2; // z height offset of boss location

module CHF_outside() {
  difference() {
   union() {
    translate([-CCW/2,-CCL/2,CCFZoff]) 
		cube([CCW,CCL,CCFH]); // back body of housing
    rotate([0,0,90]) translate([0,(CCL/2+CCFB),CCFZoff + CCFBZ]) rotate([90,0,0])
		rotate([0,0,45]) cylinder(d=CCFBOD,h=CCL+CCFB*2,$fn=4); // side boss

   }
   translate([-CCW/2+CCFT,-CCL/2+CCFT,CCFZoff-CCFT]) 
		cube([CCW-CCFT*2,CCL-CCFT*2,CCFH]); // interior cutout of housing
   cylinder(d=CMLOD+slop*2,h=20,$fn=fn); // for M12 lens housing
   rotate([0,0,90]) {
    translate([0,-CCL/2,CCFZoff + CCFBZ]) rotate([90,0,0])
		rotate([0,0,90])  cylinder(d=CCFBID,h=CCL+(eps*CCFB)*2,$fn=6); // side hex boss
    translate([0,CCL/2,CCFZoff + CCFBZ]) rotate([-90,0,0])
		rotate([0,0,90]) cylinder(d=CCFBID,h=CCL+(eps*CCFB)*2,$fn=6); // side hex boss
    translate([0,-CCL*2,CCFZoff + CCFBZ]) rotate([-90,0,0])
       cylinder(d=MHOD,h=CCL*4,$fn=fn); // side M3 through-hole
    }
  }
}

module CHF() {
 difference() {
  union() {
    CHF_outside();
    translate([0,0,10.6]) CHB_Holes(6,10);  // posts for M3 mounting holes
  }
    CHB_Holes(); // 4x mounting holes
 }
}

SHID = 3.0;  // ID of screw hole (note ID will be "slop" smaller)

// mounting screw bosses in 4 corners of camera back
module CHB_Boss() {
   union() {
	translate([(CCW/2)-BS-BSO,-CCL/2+BSO,-(BS/2)])
       cube([BS,BS,CCBD+CCBF-CBH]); // boss for mounting screw
	translate([(CCW/2)-BS-BSO,CCL/2-BS-BSO,-(BS/2)])
       cube([BS,BS,CCBD+CCBF-CBH]); // boss for mounting screw
	translate([-(CCW/2)+BSO,-CCL/2+BSO,-(BS/2)])
       cube([BS,BS,CCBD+CCBF-CBH]); // boss for mounting screw
	translate([-(CCW/2)+BSO,CCL/2-BS-BSO,-(BS/2)])
       cube([BS,BS,CCBD+CCBF-CBH]); // boss for mounting screw
   }
}

module CHB_Holes(diam=SHID,len=50) { // M3 mounting holes
  union() {
  translate([MHCC/2,MHCC/2,-BS])
 	cylinder(r=diam/2,h=len,$fn=20);  // hole for M3 mounting screw
  translate([-MHCC/2,MHCC/2,-BS])
 	cylinder(r=diam/2,h=len,$fn=20);  // hole for M3 mounting screw
  translate([MHCC/2,-MHCC/2,-BS])
 	cylinder(r=diam/2,h=len,$fn=20);  // hole for M3 mounting screw
  translate([-MHCC/2,-MHCC/2,-BS])
 	cylinder(r=diam/2,h=len,$fn=20);  // hole for M3 mounting screw
   }
}


module CameraHousingBack() {
 difference() {
  union() {
    CHB_outside();
    CHB_Boss();
  }
  CHB_Holes();
 }
}

// ================================================
// ==  U-bracket (pan-tilt motion) for camera case


BIW = 44.6;  // width of opening across U bracket
BTH = 2.5; // thickness of U bracket
BWD = 10; // width of U bracket arms (z axis)
BLT = 5; // bracket arm extension above center of pivot
BCL = 6; // bracket clearance below edge of case  (case y width = CCL)
BZoff = 3; // z-offset of entire bracket

module bracket() {
XOD = BIW+2*BTH;
 difference() {
  union() {
    translate([-XOD/2,-BLT,0]) cube([XOD, CCL/2 + BLT + BCL+BTH, BWD]);
  }
  translate([BIW/2-eps,-BWD+3,-BWD/4.8]) rotate([45,0,0]) cube([BTH+2*eps,BWD,BWD]); //notch
  translate([-BIW-BTH,0,0]) translate([BIW/2-eps,-BWD+3,-BWD/4.8]) 
	rotate([45,0,0]) cube([BTH+2*eps,BWD,BWD]); //notch

  translate([-BIW/2,-BLT-eps,-eps]) cube([BIW, CCL/2 + BLT + BCL, BWD+2*eps]);
  translate([-100,0,BWD/2]) rotate([0,90,0]) 
		cylinder(d=MHOD,h=200,$fn=20); // camera pivot (horizontal)
  translate([0,0,BWD/2]) rotate([-90,0,0]) 
		cylinder(d=MHOD,h=200,$fn=20); // center U-bracket pivot (vertical)
 }
 translate([BIW/2,+BCL+CCL/2,0]) cylinder(r=BTH,h=BWD,$fn=20); // edge fillet
 translate([-BIW/2,+BCL+CCL/2,0]) cylinder(r=BTH,h=BWD,$fn=20); // edge fillet
} // end module bracket

// CamAssy();  // just the M12 camera board model


translate([0,0,BZoff]) color("green") bracket(); // U-bracket (pan/tilt)


difference() {
  union() {
     translate([0,0,0.95]) color("grey") CamAssy();
     color("blue") CameraHousingBack();
    // rotate([180,0,0]) CHF();
     CHF();
  }
  // translate([MHCC/2,0,-50]) cube([100,100,100]); // cutaway DEBUG
}


